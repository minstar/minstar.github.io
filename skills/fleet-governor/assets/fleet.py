#!/usr/bin/env python3
"""Supervise every long-running thing at once: Slurm jobs and the retry loops that feed them.

The gap this fills: an autoretry loop is right to retry a *preempted* job and wrong to retry a
*deterministic* one, and nothing in the stack tells them apart. EXP-001 measured the cost of that
confusion at 224 single-digit-second resubmissions across three arms.

    python3 fleet.py                 # health table for everything alive
    python3 fleet.py --since 3days   # widen the sacct window (default 2days)
    python3 fleet.py --json

It only ever *reports*. Killing a job or a loop is a human decision, so the tool prints the exact
command and stops there.

Exit 0 = nothing needs attention. Exit 1 = at least one FUTILE or ORPHAN finding.
"""
import argparse
import json
import os
import re
import subprocess
import sys

USER = os.environ.get("USER", "")
# Supervisor loops are shell scripts that resubmit; exclude the agent's own shell wrappers.
LOOP_PAT = re.compile(r"\b(autoretry|auto_retry|watch_|driver_|fleet_|_loop)\w*\.sh\b|\bautoretry\.sh\b")
AGENT_NOISE = re.compile(r"claude/shell-snapshots|shopt -u extglob|builtin unalias")
FAST = re.compile(r"^00:00:0[0-9]$")


def sh(cmd):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return p.stdout
    except Exception:
        return ""


def squeue_jobs():
    out = sh('squeue -u %s -h -o "%%i|%%j|%%T|%%M|%%P"' % USER)
    jobs = []
    for ln in out.strip().splitlines():
        f = ln.split("|")
        if len(f) >= 5:
            jobs.append({"jobid": f[0].strip(), "name": f[1].strip(), "state": f[2].strip(),
                         "elapsed": f[3].strip(), "partition": f[4].strip()})
    return jobs


def loops():
    out = sh("ps -eo pid,etime,args")
    found = []
    for ln in out.splitlines()[1:]:
        parts = ln.strip().split(None, 2)
        if len(parts) < 3:
            continue
        pid, etime, cmd = parts
        if AGENT_NOISE.search(cmd) or not LOOP_PAT.search(cmd):
            continue
        m = LOOP_PAT.search(cmd)
        found.append({"pid": pid, "etime": etime, "script": m.group(0), "cmd": cmd[:180]})
    return found


def history(name, since):
    """Recent terminal states for a job name, newest first."""
    out = sh('sacct -u %s -S %s --name=%s --format=JobID%%14,State%%16,ExitCode%%8,Elapsed%%10 '
             '--noheader' % (USER, since, name))
    rows = []
    for ln in out.splitlines():
        f = ln.split()
        if len(f) < 4 or "." in f[0]:            # drop .batch/.extern/.0 steps
            continue
        rows.append({"jobid": f[0], "state": f[1], "exit": f[2], "elapsed": f[3]})
    return rows


def classify(name, rows):
    """Verdict for one job name over its recent history."""
    if not rows:
        return {"verdict": "NEW", "detail": "no terminal states in window", "counts": {}}
    fast = [x for x in rows if x["state"] == "FAILED" and FAST.match(x["elapsed"])]
    comp = [x for x in rows if x["state"] == "COMPLETED"]
    pre = [x for x in rows if x["state"] in ("PREEMPTED", "CANCELLED", "NODE_FAIL", "TIMEOUT")]
    slow_fail = [x for x in rows if x["state"] == "FAILED" and not FAST.match(x["elapsed"])]
    counts = {"fast_fail": len(fast), "completed": len(comp),
              "preempt_or_timeout": len(pre), "slow_fail": len(slow_fail), "total": len(rows)}

    # The signature that matters: the most recent attempts are ALL deterministic fast-fails.
    tail = rows[-4:] if len(rows) >= 4 else rows
    tail_fast = [x for x in tail if x["state"] == "FAILED" and FAST.match(x["elapsed"])]
    if len(tail_fast) >= 2 and len(tail_fast) == len(tail):
        exits = {x["exit"] for x in tail_fast}
        return {"verdict": "FUTILE", "counts": counts,
                "detail": "last %d attempts all failed in <10s (exit %s) — deterministic; "
                          "retrying cannot clear it" % (len(tail_fast), ",".join(sorted(exits)))}
    if len(fast) >= 5 and not comp:
        return {"verdict": "FUTILE", "counts": counts,
                "detail": "%d fast-fails and no completion in window" % len(fast)}
    if len(fast) >= 5 and comp:
        return {"verdict": "WASTEFUL", "counts": counts,
                "detail": "%d fast-fails alongside %d completion(s) — real work is landing, but a "
                          "deterministic error is being resubmitted" % (len(fast), len(comp))}
    if len(pre) >= 1 and not fast:
        return {"verdict": "HEALTHY", "counts": counts,
                "detail": "%d preemption/timeout — expected on a preemptible partition" % len(pre)}
    return {"verdict": "HEALTHY", "counts": counts,
            "detail": "%d completed, %d fast-fail" % (len(comp), len(fast))}


def main():
    ap = argparse.ArgumentParser(description="Report on Slurm jobs and the retry loops feeding them.")
    ap.add_argument("--since", default="2days", help="sacct window, e.g. 2days / 2026-08-10")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    since = a.since
    if re.match(r"^\d+days?$", since):
        n = re.sub(r"\D", "", since)
        since = sh("date -d '%s days ago' +%%Y-%%m-%%d" % n).strip() or "now-2days"

    running = squeue_jobs()
    sups = loops()
    names = sorted({j["name"] for j in running})

    report = []
    for n in names:
        rows = history(n, since)
        c = classify(n, rows)
        c["name"] = n
        c["running"] = [j for j in running if j["name"] == n]
        report.append(c)

    bad = [x for x in report if x["verdict"] in ("FUTILE", "WASTEFUL")]
    # A loop that matches no queued job is a candidate orphan. Match on the WHOLE command line, not
    # the script filename: these loops take the job name as an argument (`autoretry.sh <name> ...`),
    # so filename-only matching flagged live, healthy supervisors as orphans.
    # Generic words match by accident: an unrelated path containing `eval` "matched" a queued job
    # whose name also contained `eval`, and that spurious match hid a genuine 11-day-old orphan
    # watcher. Only distinctive tokens count.
    STOP = {"eval", "evals", "train", "test", "run", "runs", "job", "jobs", "log", "logs", "tmp",
            "temp", "data", "model", "models", "base", "main", "work", "workspace", "scratchpad",
            "claude", "private", "home", "user", "bash", "sh", "py", "out", "err", "watch", "auto",
            "retry", "autoretry", "step", "steps", "ckpt", "checkpoint", "node", "gpu", "slurm"}

    def distinctive(s):
        return {t for t in re.findall(r"[a-z0-9_]{4,}", s.lower()) if t not in STOP}

    orphans = []
    job_toks = [distinctive(n) for n in names]
    for s in sups:
        cmd_toks = distinctive(s["cmd"])
        matched = bool(names) and any(jt & cmd_toks for jt in job_toks)
        # Age is the second, independent signal: a supervisor that has outlived any plausible run
        # is worth surfacing even if a token happens to line up.
        stale = bool(re.match(r"^\d+-", s["etime"])) and int(s["etime"].split("-")[0]) >= 3
        if not matched or stale:
            s = dict(s, reason=("stale: alive %s" % s["etime"]) if stale
                     else "no queued job matches this loop")
            orphans.append(s)

    if a.json:
        print(json.dumps({"since": since, "jobs": report, "loops": sups, "orphans": orphans},
                         indent=2, ensure_ascii=False))
        return 1 if (bad or orphans) else 0

    print("fleet report  (sacct window from %s)\n" % since)
    print("  %-34s %-9s %6s %5s %6s  %s" % ("job name", "verdict", "fast", "comp", "preempt", "running"))
    for x in report:
        c = x["counts"]
        print("  %-34s %-9s %6s %5s %6s  %s"
              % (x["name"][:34], x["verdict"], c.get("fast_fail", "-"), c.get("completed", "-"),
                 c.get("preempt_or_timeout", "-"),
                 ",".join("%s/%s" % (j["jobid"], j["elapsed"]) for j in x["running"]) or "-"))
        if x["verdict"] in ("FUTILE", "WASTEFUL"):
            print("      %s" % x["detail"])

    print("\nsupervisor loops alive: %d" % len(sups))
    for s in sups:
        print("  pid %-9s up %-11s %s" % (s["pid"], s["etime"], s["script"]))
    if orphans:
        print("\nORPHAN / STALE loops:")
        for s in orphans:
            print("  pid %-9s up %-11s %-26s %s"
                  % (s["pid"], s["etime"], s["script"], s.get("reason", "")))

    if bad or orphans:
        print("\nneeds a decision:")
        for x in bad:
            print("  %-34s %s" % (x["name"], x["detail"]))
            print("      inspect: tail -20 $(ls -t **/logs/slurm_%s_*.log | head -1)" % x["name"])
        for s in orphans:
            print("  orphan loop pid %s — inspect its log before killing: kill %s" % (s["pid"], s["pid"]))
        print("\nThis tool does not kill anything. Read the log, then decide.")
    else:
        print("\nnothing needs attention.")
    return 1 if (bad or orphans) else 0


if __name__ == "__main__":
    sys.exit(main())
