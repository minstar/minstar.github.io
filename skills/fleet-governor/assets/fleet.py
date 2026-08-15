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
import datetime
import json
import os
import re
import subprocess
import sys
import time

USER = os.environ.get("USER", "")
# Supervisor loops are shell scripts that resubmit; exclude the agent's own shell wrappers.
# `.chain_*` / `.retry_*` are hidden sentinel/probe chains — supervisors too (2026-08-15: they
# were invisible to this tool while their sibling autoretry loops were being misflagged).
LOOP_PAT = re.compile(r"\b(autoretry|auto_retry|watch_|driver_|fleet_|_loop)\w*\.sh\b"
                      r"|\bautoretry\.sh\b|\.(?:chain|retry)_\w+\.sh\b")
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


# ---------------------------------------------------------------- loop <-> job association
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


def version_toks(s):
    """Arm/version tokens (`v36`, `v36s`, `v2b`), boundary-delimited.

    2026-08-15, three false "orphan" flags in one morning: job `<rl-run>-v36` vs loop
    `autoretry_v36.sh`. `v36` is 3 chars — below distinctive()'s 4-char floor — and `v36s` is
    4 chars — below linked()'s 5-char containment floor — so version-suffixed arms could NEVER
    link to their loops, while long word tokens (`perfroll`, `neweval`) linked fine. Version
    tokens are short but maximally distinctive; they get their own exact-match channel.
    Boundary-aware so `v36` does NOT cross-link with `v36s`.
    """
    return set(re.findall(r"(?<![a-z0-9])v\d+[a-z]*(?![a-z0-9])", s.lower()))


def loop_meta(pid, script, cmd):
    """Ground truth about a loop from /proc and its own script text.

    A supervisor announces itself: bash holds the running script on fd 255, its stdout/stderr
    point at its log, and the script declares the JOBNAME it submits and its poll cadence.
    Reading those beats guessing from command-line tokens.
    """
    meta = {"script_path": None, "log_path": None, "log_mtime": None, "poll": 300,
            "jobnames": []}
    for fd in ("1", "2"):
        try:
            tgt = os.readlink("/proc/%s/fd/%s" % (pid, fd))
            if os.path.isfile(tgt):
                mt = os.path.getmtime(tgt)
                if meta["log_mtime"] is None or mt > meta["log_mtime"]:
                    meta["log_mtime"], meta["log_path"] = mt, tgt
        except OSError:
            pass
    path = None
    try:
        cand = os.readlink("/proc/%s/fd/255" % pid)          # bash's own script fd
        if cand.endswith(".sh") and os.path.isfile(cand):
            path = cand
    except OSError:
        pass
    if path is None:
        try:
            cwd = os.readlink("/proc/%s/cwd" % pid)
            mm = re.search(r"(\S*%s)" % re.escape(script), cmd)
            if mm and os.path.isfile(os.path.join(cwd, mm.group(1))):
                path = os.path.join(cwd, mm.group(1))
        except OSError:
            pass
    meta["script_path"] = path
    if path:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except OSError:
            txt = ""
        polls = [int(x) for x in re.findall(r"POLL:-(\d+)", txt)]
        polls += [int(x) for x in re.findall(r"(?m)^\s*POLL=(\d+)\s*$", txt)]
        polls += [int(x) for x in re.findall(r"\bsleep\s+(\d+)", txt)]
        if polls:
            meta["poll"] = max(60, min(3600, max(polls)))
        names = re.findall(r"JOBNAME=\$\{JOBNAME:-([^}\s\"']+)\}", txt)
        names += re.findall(r"(?m)^\s*JOBNAME=([A-Za-z0-9._-]+)\s*$", txt)
        names += [m for m in re.findall(r"(?:sbatch|squeue)[^\n]*?\s-[Jn]\s+\"?([A-Za-z0-9._-]+)",
                                        txt)]
        meta["jobnames"] = sorted({n for n in names if "$" not in n})
    return meta


def recent_end(name, since, window, now):
    """Did a job with this exact name end within `window` seconds (or is one still in sacct)?

    Covers the race where fleet.py runs in the gap between a job dying and its loop's next poll
    tick: squeue is empty, but sacct shows the arm was alive minutes ago — the loop is a
    supervisor about to resubmit, not an orphan.
    """
    out = sh('sacct -u %s -S %s --name=%s -X --format=End%%20,State%%16 --noheader'
             % (USER, since, name))
    for ln in out.splitlines():
        f = ln.split()
        if not f:
            continue
        if f[0] in ("Unknown", "None"):
            return True                                       # still live per sacct
        try:
            t = time.mktime(time.strptime(f[0], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            continue
        if now - t <= window:
            return True
    return False


def assess_loop(s, meta, names, job_toks, since, now=None):
    """Supervisor-vs-orphan decision for one live loop. Pure given (s, meta, names).

    A loop is a SUPERVISOR when its associated jobname or log shows life within its own poll
    window: (1) a jobname its script declares matches a queued job, (2) distinctive-token link,
    (3) version-token link (v36 <-> autoretry_v36.sh), (4) its declared job ended within the
    window (resubmit imminent), or (5) its log was written within the window (covers loops just
    started — they write their start line). A genuine orphan — loop alive, job/stamps gone AND
    no recent log lines — matches none of these and still flags.
    """
    now = time.time() if now is None else now
    window = 2 * meta["poll"] + 60
    cmd_toks = distinctive(s["cmd"])
    declared = meta.get("jobnames") or []
    by_name = any(d == n or d in n or n in d for d in declared for n in names)
    by_tok = bool(names) and any(linked(jt, cmd_toks) for jt in job_toks)
    vt = version_toks(s["cmd"] + " " + (meta.get("script_path") or ""))
    by_ver = bool(vt) and any(version_toks(n) & vt for n in names)
    log_age = None if meta["log_mtime"] is None else now - meta["log_mtime"]
    by_log = log_age is not None and log_age <= window
    by_hist = (not (by_name or by_tok or by_ver or by_log) and
               any(recent_end(d, since, window, now) for d in declared))
    supervisor = by_name or by_tok or by_ver or by_log or by_hist
    evidence = [e for e, on in (("jobname", by_name), ("token", by_tok), ("version", by_ver),
                                ("log<%ds" % window, by_log), ("recent-end", by_hist)) if on]
    # Age stays an independent signal — a token CAN line up by accident — but hard evidence
    # (declared jobname in the queue, or a log written this poll window) overrides it: a 4-day
    # loop actively supervising its queued job is doing its job, not outliving it.
    days = int(s["etime"].split("-")[0]) if re.match(r"^\d+-", s["etime"]) else 0
    stale = days >= 3 and not (by_name or by_log or by_hist)
    if supervisor and not stale:
        reason = ""
    elif stale:
        reason = "stale: alive %s with no queue/log evidence this poll window" % s["etime"]
    else:
        quiet = "no log" if log_age is None else "log quiet %ds" % int(log_age)
        reason = ("no queued job matches and %s (> %ds poll window)" % (quiet, window))
    return {"supervisor": supervisor and not stale, "reason": reason, "window": window,
            "evidence": evidence, "declared": declared}


def history(name, since):
    """Recent terminal states for a job name, newest first."""
    # --parsable2 rather than column widths: `State` can be "CANCELLED by 12345", which whitespace
    # splitting tears into two fields and shifts every column after it.
    out = sh('sacct -u %s -S %s --name=%s --parsable2 --noheader '
             '--format=JobID,State,ExitCode,Elapsed,End' % (USER, since, name))
    rows = []
    for ln in out.splitlines():
        f = ln.split("|")
        if len(f) < 5 or "." in f[0]:            # drop .batch/.extern/.0 steps
            continue
        end = None
        try:                                      # sacct writes Unknown while a job is still live
            end = datetime.datetime.strptime(f[4].strip(), "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
        rows.append({"jobid": f[0], "state": f[1].split()[0] if f[1] else "",
                     "exit": f[2], "elapsed": f[3], "end": end})
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


def script_repaired_since(rows, running):
    """(True, detail) when the submission script was edited AFTER the last failure.

    FUTILE reads only the failure history in the window, so it cannot see the most common way a
    deterministic failure actually gets resolved here: the owner fixes the script and resubmits.
    On 2026-08-16 two arms were flagged FUTILE on two genuine exit-1 failures while their scripts
    had been repaired 08:33:26 and resubmitted 23 seconds later — and a sibling job on the same
    repaired script was already past the point where the old one died. Reporting FUTILE there
    invites cancelling a fix that is working.

    Uses the live attempt's own `Command`, so it is the script that will actually run, not a guess.
    """
    if not running:
        return False, ""
    ends = [x.get("end") for x in rows if x["state"] == "FAILED" and x.get("end")]
    if not ends:
        return False, ""
    last_fail = max(ends)
    for j in running:
        jid = str(j.get("jobid") or "").split(".")[0].split("_")[0]
        if not jid.isdigit():
            continue
        out = sh("scontrol show job %s 2>/dev/null" % jid)
        m = re.search(r"Command=(\S+)", out or "")
        if not m:
            continue
        p = m.group(1)
        # <internal-root> and <shared-work-root>/private are the same tree by two mounts; only one is readable here.
        for cand in (p, p.replace("<shared-work>", "<shared-work>")):
            try:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(cand))
            except OSError:
                continue
            if mt > last_fail:
                return True, ("submission script %s was edited %s, after the last failure at %s"
                              % (os.path.basename(cand), mt.strftime("%m-%d %H:%M"),
                                 last_fail.strftime("%m-%d %H:%M")))
            break
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

    # A repair landed after the last failure. Even a deterministic cause is no longer evidence about
    # the attempt now queued, because the thing that produced it has changed.
    if fails and not comp:
        fixed, how = script_repaired_since(rows, running)
        if fixed:
            return {"verdict": "RECOVERING", "counts": counts,
                    "detail": "%d failure(s), but %s — the live attempt runs different code"
                              % (len(fails), how)}

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
    # A loop that matches no queued job — by declared jobname, distinctive/version tokens, recent
    # sacct end, or a log line within its own poll window — is a candidate orphan. Match on the
    # WHOLE command line plus what /proc and the script itself expose: filename-only and
    # word-token-only matching each flagged live, healthy supervisors as orphans
    # (2026-08-15: autoretry_v36{,s}.sh vs jobs <rl-run>-v36{,s}).
    orphans = []
    job_toks = [distinctive(n) for n in names]
    for s in sups:
        meta = loop_meta(s["pid"], s["script"], s["cmd"])
        verdict = assess_loop(s, meta, names, job_toks, since)
        s["evidence"] = ",".join(verdict["evidence"]) or "-"
        if not verdict["supervisor"]:
            orphans.append(dict(s, reason=verdict["reason"]))

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
        print("  pid %-9s up %-11s %-30s link:%s"
              % (s["pid"], s["etime"], s["script"], s.get("evidence", "-")))
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
