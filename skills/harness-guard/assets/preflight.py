#!/usr/bin/env python3
"""Pre-flight checker for Slurm submission / serving scripts.

Every check here exists because the corresponding failure actually happened. Prose reminders
did not prevent them; a check that runs every time does.

    python3 preflight.py <script.slurm> [--json] [--strict]

Exit 0 = clear to submit. Exit 1 = at least one FAIL (or a WARN under --strict).

Honesty rule: a check that cannot evaluate reports SKIP with the reason. It never reports PASS
for something it did not actually verify.
"""
import argparse
import json
import os
import re
import sys

FAIL, WARN, PASS, SKIP = "FAIL", "WARN", "PASS", "SKIP"

# Paths under these roots are visible from compute nodes; /home is NOT shared.
SHARED_ROOTS = ("<shared-work-root>/", "<shared-fs>/", "/scratch/", "/shared/")
UNSHARED_HOME = "<home>"

TRAIN_HINTS = ("torchtitan", "torchrun", "train.py", "sft", "pretrain", "grpo", "verl", "slime", "fsdp")
SERVE_HINTS = ("vllm serve", "sglang", "launch_server", "api_server", "--served-model-name")
COMPUTE_LINE = re.compile(r"\b(srun|torchrun|python3?|accelerate|deepspeed|uv run|bash)\b")


class Ctx:
    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8", errors="replace") as fh:
            self.lines = fh.read().splitlines()
        self.text = "\n".join(self.lines)
        self.low = self.text.lower()
        self.vars = self._collect_vars()

    def _collect_vars(self):
        v = {}
        for ln in self.lines:
            s = ln.strip()
            if s.startswith("#"):
                continue
            m = re.match(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$", s)
            if m:
                raw_val = m.group(2).strip()
                # `VAR=x command ...` is a bash env-prefix, not a script-level assignment —
                # collecting it poisons the table (e.g. RM_PATH="${RM_PATH}" PYTHONPATH=... python
                # swallowed the rest of the line as RM_PATH's value).
                if re.match(r"""^("[^"]*"|'[^']*'|[^\s"']+)\s+\S""", raw_val):
                    continue
                val = raw_val.strip('"').strip("'")
                # env-overridable default, VAR=${VAR:-default}: for static analysis the value IS
                # the default (EXP-001 — RM_PATH=${RM_PATH:-pkg.mod.fn} must resolve to a literal
                # so module-refs can check the module it names actually exists).
                d = re.match(r"\$\{%s:-(.*)\}$" % re.escape(m.group(1)), val)
                if d:
                    val = d.group(1).strip('"').strip("'")
                v[m.group(1)] = val
        # one-level-at-a-time expansion, bounded
        for _ in range(4):
            for k, val in list(v.items()):
                v[k] = self.expand(val, v)
        return v

    @staticmethod
    def expand(s, table):
        def sub(m):
            return table.get(m.group(1) or m.group(2), m.group(0))
        return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", sub, s)

    def sbatch(self, *names):
        """Value of an #SBATCH directive, or None."""
        for ln in self.lines:
            s = ln.strip()
            if not s.startswith("#SBATCH"):
                continue
            body = s[len("#SBATCH"):].strip()
            for n in names:
                if body.startswith(n):
                    rest = body[len(n):].lstrip()
                    if rest.startswith("="):
                        rest = rest[1:]
                    return rest.split()[0].strip('"').strip("'") if rest.split() else ""
        return None

    def has_env(self, name):
        return bool(re.search(r"(?m)^\s*export\s+%s=" % re.escape(name), self.text)) or name in self.vars

    def grep(self, pattern):
        """[(lineno, line)] for a regex, skipping comments."""
        rx = re.compile(pattern)
        out = []
        for i, ln in enumerate(self.lines, 1):
            if ln.strip().startswith("#") and not ln.strip().startswith("#SBATCH"):
                continue
            if rx.search(ln):
                out.append((i, ln.strip()))
        return out

    def is_training(self):
        # Serving takes precedence. An eval/serve script routinely names training artifacts
        # (checkpoint dirs like `..._grpo_...`, `..._sft_...`), and demanding the training env of
        # it is a false positive — the first one the hook surfaced on a real script.
        if self.is_serving():
            return False
        return any(h in self.low for h in TRAIN_HINTS)

    def is_serving(self):
        return any(h in self.low for h in SERVE_HINTS)


def r(cid, level, title, evidence="", fix=""):
    return {"id": cid, "level": level, "title": title, "evidence": evidence, "fix": fix}


# ---------------------------------------------------------------- checks

def check_partition(c):
    p = c.sbatch("-p", "--partition")
    if p is None:
        return r("partition", FAIL, "No partition declared",
                 "no #SBATCH -p/--partition line", "Add: #SBATCH -p <preemptible-partition>")
    p = Ctx.expand(p, c.vars)
    if p != "<preemptible-partition>":
        return r("partition", FAIL, "Partition is not <preemptible-partition>", "partition=%s" % p,
                 "Only <preemptible-partition> may be used; <standard-partition> is off-limits.")
    return r("partition", PASS, "partition=<preemptible-partition>")


def check_shared_storage(c):
    hard, soft = [], []
    for i, ln in enumerate(c.lines, 1):
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#SBATCH"):
            continue
        if UNSHARED_HOME not in Ctx.expand(ln, c.vars):
            continue
        expanded = Ctx.expand(ln, c.vars)
        # log destinations are written by the node but rarely block the run
        if s.startswith("#SBATCH") and ("--output" in s or "--error" in s or "-o " in s or "-e " in s):
            soft.append((i, expanded.strip()))
        elif COMPUTE_LINE.search(s) or re.match(r"(?:export\s+)?[A-Za-z_]\w*=", s):
            hard.append((i, expanded.strip()))
        else:
            soft.append((i, expanded.strip()))
    if hard:
        ev = "; ".join("L%d: %s" % (n, t[:110]) for n, t in hard[:5])
        return r("shared-storage", FAIL, "%s is not shared across Slurm nodes" % UNSHARED_HOME, ev,
                 "Move inputs/scripts/checkpoints under <shared-work> or <shared-fs>.")
    if soft:
        ev = "; ".join("L%d: %s" % (n, t[:110]) for n, t in soft[:5])
        return r("shared-storage", WARN, "%s referenced (log paths only)" % UNSHARED_HOME, ev,
                 "Confirm the node can write there; prefer a shared path for logs too.")
    return r("shared-storage", PASS, "no unshared /home paths")


def check_conda_env(c):
    envs = [m.group(1) for m in re.finditer(r"conda activate\s+(\S+)", c.text)]
    if not envs:
        if c.is_training():
            return r("conda-env", FAIL, "Training script activates no conda env", "",
                     "Training must run in the torchtitan env: conda activate torchtitan")
        return r("conda-env", SKIP, "no conda activate found and script is not training-shaped")
    envs = [Ctx.expand(e, c.vars) for e in envs]
    if c.is_training() and not any("torchtitan" in e for e in envs):
        return r("conda-env", FAIL, "Training script is not using the torchtitan env",
                 "activates: %s" % ", ".join(envs), "Training always uses the torchtitan conda env.")
    return r("conda-env", PASS, "conda env: %s" % ", ".join(envs))


PATH_RX = re.compile(r"(/(?:data|mnt|home|scratch|shared|opt)/[^\s'\"`:,)\]}$]+)")


# A path that appears ONLY inside a shell existence test is being probed, not consumed: its
# absence is the branch condition, not a stale reference. Every slime resume launcher does
# `[ -f "$LOAD_DIR/latest_checkpointed_iteration.txt" ]` to pick fresh-vs-resume, and flagging
# that as a missing input made the checker cry wolf on a correct script (2026-08-15, the
# <monorepo> A/B/C launchers). A path used in a test AND consumed elsewhere still gets flagged.
GUARD_RX = re.compile(r"(?:\[\[?\s*!?\s*-[a-zA-Z]\s|\btest\s+!?\s*-[a-zA-Z]\s)")


def check_paths_exist(c):
    cands, seen = [], set()
    guarded, consumed = set(), set()
    for i, ln in enumerate(c.lines, 1):
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#SBATCH"):
            continue
        expanded = Ctx.expand(ln, c.vars)
        is_guard = bool(GUARD_RX.search(expanded))
        for m in PATH_RX.finditer(expanded):
            _p = m.group(1).rstrip("/\\").rstrip(";,:)]}\"'")
            (guarded if is_guard else consumed).add(_p)
        for m in PATH_RX.finditer(expanded):
            raw = m.group(1)
            nxt = expanded[m.end():m.end() + 1]
            if nxt in ("$", "{"):
                # A variable follows. `.../chunks/$BENCH` still asserts that `.../chunks` exists —
                # keep the complete directory. `.../ckpt_${NAME}` does not assert anything about a
                # partial filename stem — drop it. Getting this backwards costs a real finding in
                # one direction and credibility in the other.
                if not raw.endswith("/"):
                    continue
            p = raw.rstrip("/\\").rstrip(";,:)]}\"'")
            # `%x`/`%j`/`%A` are Slurm substitutions filled in at dispatch, not paths that exist
            # now; `{name}` is a runtime format template (e.g. --save-hf .../rollout-{rollout_id}).
            if not p or "$" in p or "*" in p or "?" in p or "%" in p or "{" in p or p in seen:
                continue
            seen.add(p)
            cands.append((i, p))
    if not cands:
        return r("paths-exist", SKIP, "no literal absolute paths found to check")
    missing = [(i, p) for i, p in cands if not os.path.exists(p)]
    # a path the script itself creates is not an error
    missing = [(i, p) for i, p in missing
               if not re.search(r"mkdir\s+(-p\s+)?[^\n]*%s" % re.escape(p), c.text)]
    # nor is one that is only ever probed by an existence test (see GUARD_RX)
    missing = [(i, p) for i, p in missing if not (p in guarded and p not in consumed)]
    if missing:
        ev = "; ".join("L%d: %s" % (n, p) for n, p in missing[:6])
        return r("paths-exist", FAIL, "%d referenced path(s) do not exist" % len(missing), ev,
                 "Fix the path, or create it before submitting. Stale paths after a refactor are the "
                 "most common procedural failure here.")
    return r("paths-exist", PASS, "%d literal paths all exist" % len(cands))


def check_uv_cache(c):
    if not c.grep(r"\buv\b\s+(run|pip|venv|sync)"):
        return r("uv-cache", SKIP, "uv not used")
    if not c.has_env("UV_CACHE_DIR"):
        return r("uv-cache", FAIL, "uv used without UV_CACHE_DIR", "",
                 "On requeue a shared uv cache collides and the job FAILs immediately. "
                 "Set UV_CACHE_DIR to a per-job path under /tmp and rename the run dir on requeue.")
    return r("uv-cache", PASS, "UV_CACHE_DIR set")


def check_flashinfer(c):
    if not re.search(r"flashinfer|vllm|sglang", c.low):
        return r("flashinfer", SKIP, "no vllm/sglang/flashinfer")
    if not c.has_env("FLASHINFER_WORKSPACE_BASE"):
        return r("flashinfer", WARN, "FLASHINFER_WORKSPACE_BASE not isolated", "",
                 "A shared flashinfer JIT cache causes ninja build failures across concurrent jobs. "
                 "Point it at a per-job directory.")
    return r("flashinfer", PASS, "FLASHINFER_WORKSPACE_BASE set")


def check_rocr(c):
    if "verl" not in c.low:
        return r("rocr", SKIP, "verl not used")
    if not re.search(r"unset\s+ROCR_VISIBLE_DEVICES", c.text):
        return r("rocr", FAIL, "verl used without unsetting ROCR_VISIBLE_DEVICES", "",
                 "The cluster sets ROCR and CUDA visible devices together; verl workers die until "
                 "ROCR_VISIBLE_DEVICES is unset. Add: unset ROCR_VISIBLE_DEVICES")
    return r("rocr", PASS, "ROCR_VISIBLE_DEVICES unset")


def check_hf_home(c):
    if not re.search(r"huggingface|transformers|hf_hub|from_pretrained|HF_", c.text, re.I):
        return r("hf-home", SKIP, "no HuggingFace usage detected")
    if not c.has_env("HF_HOME"):
        return r("hf-home", WARN, "HF_HOME not set", "",
                 "Without HF_HOME the cache lands in the home dir (not shared) or a tmpfs that fills.")
    val = c.vars.get("HF_HOME", "")
    if val.startswith("/tmp"):
        return r("hf-home", WARN, "HF_HOME points at /tmp", "HF_HOME=%s" % val,
                 "/tmp is tmpfs here and has filled mid-run; use a shared or disk-backed path.")
    return r("hf-home", PASS, "HF_HOME=%s" % val)


def check_requeue(c):
    if not re.search(r"--requeue|--open-mode=append", c.text):
        return r("requeue", SKIP, "requeue not configured")
    if not re.search(r"SLURM_RESTART_COUNT|mv\s+.*run_dir|RUN_DIR=.*\$\{?SLURM_JOB_ID", c.text):
        return r("requeue", WARN, "requeue enabled without a per-attempt run dir", "",
                 "On requeue, a reused run dir collides with the previous attempt's state. "
                 "Uniquify the run dir (e.g. include SLURM_JOB_ID / SLURM_RESTART_COUNT).")
    return r("requeue", PASS, "requeue handled with a per-attempt run dir")


def check_serve_teardown(c):
    if not c.is_serving():
        return r("serve-teardown", SKIP, "not a serving script")
    return r("serve-teardown", WARN, "serving job: remember teardown", "",
             "scancel this job as soon as the consumer eval finishes — an idle server bills "
             "GPU-hours against nothing.")


def check_referenced_scripts(c):
    refs, missing = [], []
    for i, ln in enumerate(c.lines, 1):
        s = Ctx.expand(ln.strip(), c.vars)
        if s.startswith("#") and not s.startswith("#SBATCH"):
            continue
        for m in re.finditer(r"(?:sbatch|bash|sh|source|\.)\s+(/\S+\.(?:sh|slurm|py))", s):
            p = m.group(1)
            refs.append(p)
            if not os.path.exists(p):
                missing.append((i, p))
    if not refs:
        return r("script-refs", SKIP, "no absolute script references")
    if missing:
        ev = "; ".join("L%d: %s" % (n, p) for n, p in missing)
        return r("script-refs", FAIL, "referenced script(s) missing", ev,
                 "A submit wrapper pointing at a moved/renamed sbatch file silently runs the wrong "
                 "thing or dies late. Repoint it.")
    return r("script-refs", PASS, "%d referenced scripts exist" % len(refs))


MODULE_ARG = re.compile(
    r"(-m|--custom[-_]rm[-_]path|--rm[-_]module|--reward[-_]module|--rm[-_]path)"
    r"\s+['\"]?([A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+)")
SCRIPT_ARG = re.compile(r"(?<![\w/.-])([A-Za-z_][\w.-]*/[\w./-]+\.py)")


def check_python_module_refs(c):
    """Resolve python module/script references against the script's own PYTHONPATH.

    Installed after EXP-001: a three-arm run burned 224 single-digit-second resubmissions on
    ModuleNotFoundError, because the submit path derived a per-arm reward-module name from the arm
    label and that module was never created. The failure is deterministic — an autoretry loop can
    never clear it — so it has to be caught before submission, not after.
    """
    roots = []
    for m in re.finditer(r"(?:export\s+)?PYTHONPATH=([^\s;]+)", c.text):
        for part in Ctx.expand(m.group(1).strip('"').strip("'"), c.vars).split(":"):
            part = part.strip()
            if part and not part.startswith("$") and os.path.isdir(part):
                roots.append(part)
    roots.append(os.path.dirname(os.path.abspath(c.path)))
    # a submit script living INSIDE its package (<rl-run>_stop/run_*.slurm referencing
    # <rl-run>_stop.rm_*) imports relative to the package's parent at runtime
    roots.append(os.path.dirname(os.path.dirname(os.path.abspath(c.path))))
    roots = list(dict.fromkeys(roots))

    refs = []                                    # (lineno, raw, kind)
    for i, ln in enumerate(c.lines, 1):
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#SBATCH"):
            continue
        e = Ctx.expand(ln, c.vars)
        for m in MODULE_ARG.finditer(e):
            # -m names a module; the rm/reward flags name module.attr (slime convention), so the
            # import target is the PARENT of the last component.
            refs.append((i, m.group(2), "module" if m.group(1) == "-m" else "module_attr"))
        if re.search(r"\bpython3?\b|\$ENVPY|\bsrun\b|\btorchrun\b", e):
            for m in SCRIPT_ARG.finditer(e):
                p = m.group(1)
                if not p.startswith("/"):
                    refs.append((i, p, "script"))
    if not refs:
        return r("module-refs", SKIP, "no python module/script references resolvable from this script")

    missing = []
    for lineno, raw, kind in refs:
        if "$" in raw:
            continue                             # unexpanded template — cannot verify, do not claim
        if kind == "script":
            rels = [raw]
        else:
            rels = [raw.replace(".", os.sep) + ".py",
                    raw.replace(".", os.sep)]              # package dir with __init__.py
            if kind == "module_attr" and "." in raw:       # pkg.module.attr -> pkg/module.py
                rels.append(raw.rsplit(".", 1)[0].replace(".", os.sep) + ".py")
        if not any(os.path.exists(os.path.join(rt, rel)) for rt in roots for rel in rels):
            missing.append((lineno, raw, kind))

    if missing:
        ev = "; ".join("L%d: %s (%s)" % (n, raw, k) for n, raw, k in missing[:5])
        return r("module-refs", FAIL, "%d python reference(s) do not resolve" % len(missing),
                 ev + "  [roots: %s]" % ", ".join(roots[:3]),
                 "ModuleNotFoundError fails in ~2s and an autoretry loop will resubmit it forever "
                 "(EXP-001: 224 wasted submissions). Create the module or fix the name before submitting.")
    return r("module-refs", PASS, "%d python reference(s) resolve" % len(refs))


ARM_TOKEN = re.compile(r"(?<![a-z0-9])(<rl-run>[a-z0-9]+|v\d+[a-z]*)(?![a-z0-9])")
IDENTITY_VARS = ("ARM", "MODEL", "MODEL_OVERRIDE", "CKPT_DIR", "SAVE_DIR", "WANDB_GROUP",
                 "HF_DIR", "JOBNAME")
WAIVER = "# preflight: allow-cross-arm"
UNEXPANDED = re.compile(r"\$\{[^}]*\}|\$[A-Za-z_]\w*")


def _arm_cores(s):
    """Boundary-delimited arm tokens, normalized to their version core.

    `<rl-run>v36` and `v36` are the same arm; `v36` and `v36s` are NOT — that one-letter
    difference is the entire EXP-012d incident. Arm suffixes in this codebase are 0-2 letters
    (v36s, v33t); a 3+-letter tail is a glued-on word, not an arm (`v36cen` = census OF v36,
    `v2ckpt` = v2 checkpoint), so long tails are stripped back to the bare version.
    """
    cores = set()
    for tok in ARM_TOKEN.findall(s.lower()):
        m = re.search(r"(v\d+)([a-z]*)$", tok)
        if m:
            cores.add(m.group(1) if len(m.group(2)) >= 3 else m.group(0))
        else:
            cores.add(tok)
    return cores


def check_arm_consistency(c):
    """A sed-cloned script that kept the donor's identity vars measures the WRONG arm.

    Incident (EXP-012d, 2026-08-15): probe_v36s_sentinel.slurm was cloned from the v36 probe
    and kept ARM=<rl-run>v36 — three sentinel probes served and measured the v36 model's
    weights while reporting as v36s, and a training run was halted on that false evidence.
    The filename said v36s; the identity vars said v36; nothing compared them. This does.

    Waive a deliberate cross-arm reference with `# preflight: allow-cross-arm` on the line
    (or on its own line to waive the whole file).
    """
    fname_cores = _arm_cores(os.path.splitext(os.path.basename(c.path))[0])
    if not fname_cores:
        return r("arm-consistency", SKIP, "filename carries no arm/version token")
    if any(ln.strip() == WAIVER for ln in c.lines):
        return r("arm-consistency", SKIP, "waived file-wide by '%s'" % WAIVER)

    targets = []                                             # (lineno, label, raw_value)
    var_rx = re.compile(r"(?:export\s+)?(%s)=(.*)$" % "|".join(IDENTITY_VARS))
    for i, ln in enumerate(c.lines, 1):
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#SBATCH"):
            continue
        if s.startswith("#SBATCH"):
            m = re.search(r"(?:-J|--job-name)[=\s]+(\S+)", s)
            if m:
                targets.append((i, "job-name", m.group(1)))
            continue
        m = var_rx.match(s)
        if m:
            val = m.group(2).strip().strip('"').strip("'")
            d = re.match(r"\$\{%s:-(.*)\}$" % m.group(1), val)   # VAR=${VAR:-default} -> default
            if d:
                val = d.group(1).strip('"').strip("'")
            targets.append((i, m.group(1), val))
        for jm in re.finditer(r"\bsbatch\b[^\n]*?(?:-J|--job-name)[=\s]+[\"']?([A-Za-z0-9._$\{\}-]+)", s):
            targets.append((i, "sbatch -J", jm.group(1)))

    if not targets:
        return r("arm-consistency", SKIP, "no identity-bearing assignments found")

    bad = []
    for i, label, raw in targets:
        if WAIVER in c.lines[i - 1]:
            continue
        # expand what the script defines; blank out what stays unresolved so a template var
        # can neither hide a stale literal token nor fabricate one across a join
        val = UNEXPANDED.sub(" ", Ctx.expand(raw, c.vars))
        cores = _arm_cores(val)
        if cores and not (cores & fname_cores):
            bad.append((i, label, raw, cores))
    if bad:
        ev = "; ".join("L%d: %s=%s carries %s, filename says %s"
                       % (i, label, raw[:60], "/".join(sorted(k)), "/".join(sorted(fname_cores)))
                       for i, label, raw, k in bad[:5])
        return r("arm-consistency", FAIL,
                 "identity var(s) carry a different arm than the filename", ev,
                 "Cloned script kept the donor's identifiers (EXP-012d: three probes measured "
                 "the wrong model's weights). Update ARM/MODEL/CKPT_DIR/... to match the "
                 "filename's arm, or waive deliberately with '%s'." % WAIVER)
    return r("arm-consistency", PASS,
             "identity vars agree with filename arm token(s): %s" % "/".join(sorted(fname_cores)))


RAY_SHELL_META_RX = re.compile(r"<\||\|>")


def check_ray_argv_shell(c):
    """`ray job submit -- <argv>` does NOT exec argv.

    Ray re-joins the entrypoint with subprocess.list2cmdline — the WINDOWS quoting function,
    which quotes only on whitespace — and the job manager runs the result under /bin/sh
    (ray/dashboard/modules/job/cli.py:313). Any value carrying POSIX shell metacharacters and no
    spaces therefore reaches sh RAW. Installed 2026-08-15 after jobs 68024/68025/68026 all died
    in under 60s on `--rollout-stop <|im_end|>` -> "/bin/sh: 1: Syntax error: | unexpected",
    which fires AFTER ray accepts the job and after the whole Ray/Megatron bring-up. The same
    path silently eats backslashes: `self_attention\\.` arrives as `self_attention.`, a regex
    whose dot matches any character.

    Quoting cannot be judged by eye here — `"${VAR:-'<|x|>'}"` is safe and `'<|x|>'` is not, and
    shlex-based round-trip checks pass on the argv that kills the job. So this does not try to
    prove the quoting; it requires the script to run the /bin/sh oracle at launch
    (``argv_survives_ray_shell``, <monorepo>_rl/lib_argv_guard.sh), or to say out loud that it
    has been checked with ``# preflight: argv-guarded``.
    """
    # The invocation is rarely the literal `ray job submit` — the launchers here call
    # `"${RAY_BIN}" job submit` / `${VENV}/bin/ray job submit`, so anchor on `job submit`
    # plus any mention of ray rather than on the three-word form.
    if not (c.grep(r"\bjob\s+submit\b") and c.grep(r"(?i)\bray\b")):
        return r("ray-argv-shell", SKIP, "no ray job submission in this script")
    hits = [(i, ln.strip()[:90]) for i, ln in enumerate(c.lines, 1)
            if RAY_SHELL_META_RX.search(ln) and not ln.strip().startswith("#")]
    if not hits:
        return r("ray-argv-shell", SKIP, "no shell-metacharacter argument values found")
    if c.grep(r"argv_survives_ray_shell") or c.grep(r"#\s*preflight:\s*argv-guarded"):
        return r("ray-argv-shell", PASS,
                 "%d metachar arg(s), guarded by the /bin/sh round-trip check" % len(hits))
    ev = "; ".join("L%d: %s" % (n, s) for n, s in hits[:4])
    return r("ray-argv-shell", FAIL,
             "%d ray-entrypoint arg(s) carry shell metacharacters with no argv guard" % len(hits),
             ev,
             "ray joins argv with list2cmdline and runs it under /bin/sh, so `<|im_end|>` becomes "
             "a redirect+pipe and the job dies ~40s in. Source "
             "<monorepo>_rl/lib_argv_guard.sh and call `argv_survives_ray_shell "
             "\"${TRAIN_ARGV[@]}\" || exit 1` before `ray job submit`, passing protected values "
             "with LITERAL single quotes (--rollout-stop \"'<|im_end|>'\"). If you have verified "
             "it another way, mark the script `# preflight: argv-guarded`.")


CHECKS = [check_partition, check_shared_storage, check_conda_env, check_paths_exist,
          check_uv_cache, check_flashinfer, check_rocr, check_hf_home, check_requeue,
          check_serve_teardown, check_referenced_scripts, check_python_module_refs,
          check_arm_consistency, check_ray_argv_shell]


def main():
    ap = argparse.ArgumentParser(description="Pre-flight a Slurm submission/serving script.")
    ap.add_argument("script")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat WARN as blocking")
    a = ap.parse_args()

    if not os.path.exists(a.script):
        print("preflight: no such script: %s" % a.script, file=sys.stderr)
        return 2

    c = Ctx(a.script)
    results = []
    for fn in CHECKS:
        try:
            results.append(fn(c))
        except Exception as exc:                                   # a broken check must not pass silently
            results.append(r(fn.__name__, SKIP, "check errored", repr(exc),
                             "Fix the checker; this condition was NOT verified."))

    fails = [x for x in results if x["level"] == FAIL]
    warns = [x for x in results if x["level"] == WARN]

    if a.json:
        print(json.dumps({"script": a.script, "results": results,
                          "fail": len(fails), "warn": len(warns)}, indent=2, ensure_ascii=False))
    else:
        mark = {FAIL: "FAIL", WARN: "WARN", PASS: "ok  ", SKIP: "--  "}
        print("pre-flight: %s" % a.script)
        for x in results:
            print("  [%s] %-15s %s" % (mark[x["level"]], x["id"], x["title"]))
            if x["evidence"]:
                print("           %s" % x["evidence"])
            if x["fix"] and x["level"] in (FAIL, WARN):
                print("           -> %s" % x["fix"])
        print("\n%d FAIL, %d WARN, %d checked" % (len(fails), len(warns), len(results)))
        if fails:
            print("DO NOT SUBMIT until the FAILs are resolved.")
        elif warns:
            print("Clear to submit once each WARN has been read and accepted.")
        else:
            print("Clear to submit.")

    return 1 if (fails or (a.strict and warns)) else 0


if __name__ == "__main__":
    sys.exit(main())
