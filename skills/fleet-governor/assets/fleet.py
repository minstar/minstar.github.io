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
    """Supervisor loops belonging to THIS user only.

    `ps -eo` lists every user on the node. An earlier version used it and surfaced a colleague's
    11-day watcher as if it were ours — a report that invited killing someone else's live process.
    Scope to $USER, and carry the owner in the record so the output can never be misread again.
    """
    if not USER:
        return []
    out = sh("ps -u %s -o pid=,user=,etime=,args=" % USER)
    found = []
    for ln in out.splitlines():
        parts = ln.strip().split(None, 3)
        if len(parts) < 4:
            continue
        pid, user, etime, cmd = parts
        if user != USER:                          # belt and braces
            continue
        if AGENT_NOISE.search(cmd) or not LOOP_PAT.search(cmd):
            continue
        m = LOOP_PAT.search(cmd)
        found.append({"pid": pid, "user": user, "etime": etime,
                      "script": m.group(0), "cmd": cmd[:180]})
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


def elapsed_secs(s):
    """`[DD-]HH:MM:SS` or `MM:SS` -> seconds; None if unparseable."""
    try:
        days = 0
        if "-" in s:
            d, s = s.split("-", 1)
            days = int(d)
        parts = [int(x) for x in s.split(":")]
        while len(parts) < 3:
            parts.insert(0, 0)
        return days * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]
    except (ValueError, AttributeError):
        return None


def deterministic(fails):
    """A failure cluster is deterministic when the attempts are IDENTICAL, not when they are fast.

    The first version keyed only on `elapsed < 10s`, and called a job HEALTHY that had failed 40
    times with zero completions — because each attempt booted a vLLM server for ~95s before hitting
    a missing data directory. Duration is a property of how far the job gets before the same wall;
    what marks determinism is that every attempt hits the same wall the same way.
    """
    if len(fails) < 3:
        return False, ""
    exits = {x["exit"] for x in fails}
    if len(exits) != 1:
        return False, ""
    secs = [e for e in (elapsed_secs(x["elapsed"]) for x in fails) if e is not None]
    if len(secs) < 3:
        return False, ""
    lo, hi, mid = min(secs), max(secs), sorted(secs)[len(secs) // 2]
    if hi - lo <= max(10, 0.25 * max(mid, 1)):
        return True, ("%d attempts, identical exit %s, elapsed %ds-%ds (no spread)"
                      % (len(fails), exits.pop(), lo, hi))
    return False, ""


def classify(name, rows, running=None):
    """Verdict for one job name over its recent history, in light of what is running now."""
    if not rows:
        return {"verdict": "NEW", "detail": "no terminal states in window", "counts": {}}
    fails = [x for x in rows if x["state"] == "FAILED"]
    fast = [x for x in fails if FAST.match(x["elapsed"])]
    comp = [x for x in rows if x["state"] == "COMPLETED"]
    pre = [x for x in rows if x["state"] in ("PREEMPTED", "CANCELLED", "NODE_FAIL", "TIMEOUT")]
    counts = {"fast_fail": len(fast), "completed": len(comp), "preempt_or_timeout": len(pre),
              "slow_fail": len(fails) - len(fast), "total": len(rows)}

    det, why = deterministic(fails)

    # A live attempt that has already outlasted every failure has cleared whatever wall they hit.
    # Without this, one 2-second fast-fail plus a healthy 3-minute rerun read as FUTILE — a verdict
    # that would have had someone kill a job that was working.
    longest_fail = max([e for e in (elapsed_secs(x["elapsed"]) for x in fails) if e is not None],
                       default=0)
    live = max([e for e in (elapsed_secs(j["elapsed"]) for j in (running or [])) if e is not None],
               default=0)
    if fails and live > max(longest_fail * 2, longest_fail + 60):
        return {"verdict": "RECOVERING", "counts": counts,
                "detail": "%d past failure(s) (longest %ds) but a live attempt is at %ds — it is "
                          "past the wall they hit" % (len(fails), longest_fail, live)}

    # Nothing is landing. This dominates every other reading — but one failure is an incident, not a
    # pattern, so it does not earn a verdict that invites cancelling the arm.
    if len(fails) >= 2 and not comp:
        d = ("deterministic — %s; retrying cannot clear it" % why) if det else \
            ("%d failure(s), zero completions in window" % len(fails))
        return {"verdict": "FUTILE", "counts": counts, "detail": d}
    if fails and not comp:
        return {"verdict": "WATCH", "counts": counts,
                "detail": "1 failure, no completion yet — an incident, not yet a pattern"}

    # Work is landing, but a repeated identical failure is also being resubmitted — the one that
    # hides, because the completions make the arm look fine.
    if det and comp:
        return {"verdict": "WASTEFUL", "counts": counts,
                "detail": "%s, alongside %d completion(s) — real work is landing while a "
                          "deterministic error is resubmitted" % (why, len(comp))}
    if len(fails) >= 5 and comp:
        return {"verdict": "WASTEFUL", "counts": counts,
                "detail": "%d failures alongside %d completion(s) — check whether one cause repeats"
                          % (len(fails), len(comp))}
    if pre and not fails:
        return {"verdict": "HEALTHY", "counts": counts,
                "detail": "%d preemption/timeout, no failures — expected on a preemptible partition"
                          % len(pre)}
    return {"verdict": "HEALTHY", "counts": counts,
            "detail": "%d completed, %d failure(s)" % (len(comp), len(fails))}


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
        c = classify(n, rows, [j for j in running if j["name"] == n])
        c["name"] = n
        c["running"] = [j for j in running if j["name"] == n]
        report.append(c)

    bad = [x for x in report if x["verdict"] in ("FUTILE", "WASTEFUL")]   # WATCH/RECOVERING inform, not demand
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

    def linked(job_toks, cmd_toks):
        """Exact token overlap, OR one token containing another (>=5 chars).

        `autoretry_perfroll.sh` feeds jobs named `perfroll-0..3`; exact-token matching missed it and
        called a healthy live supervisor an orphan. Driver scripts routinely embed the job name.
        """
        if job_toks & cmd_toks:
            return True
        for j in job_toks:
            if len(j) < 5:
                continue
            for c in cmd_toks:
                if j in c or (len(c) >= 5 and c in j):
                    return True
        return False

    orphans = []
    job_toks = [distinctive(n) for n in names]
    for s in sups:
        cmd_toks = distinctive(s["cmd"])
        matched = bool(names) and any(linked(jt, cmd_toks) for jt in job_toks)
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
