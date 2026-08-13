# references/ — per-benchmark evidence base

One file per benchmark. Each links a **data-construction lever** (what raises the
score, per the target reports) or a **failure mode** (what poisons training data)
to a concrete detector, with a citation URL. This is what turns an intuition into
either a tuned threshold or a new detector.

## Research workflow (Workflow C)
For a target benchmark `B`:
1. `web_search` for: the **frontier model reports / system cards** that report
   `B` (e.g. "<model> system card <B>"), and **papers citing `B`** on
   contamination, leakage, calibration, or search-behavior.
2. `web_fetch`/extract the most relevant URLs. Pull (a) data-construction levers
   the report *attributes gains to*, and (b) named failure modes.
3. Fill `references/<B>.md` from the template below, **with citation URLs**.
4. Map each failure mode → an existing detector (and its threshold) or note a
   new detector to add. Record whether the literature confirms each open
   intuition and any proposed fix.

## Per-benchmark file template
```markdown
# <Benchmark>

## What it measures
<one paragraph: task, metric, answer format (short string? table? report?)>

## Data-construction levers  (→ to RAISE the score)
- <lever> — <why it helps> — [report/paper](URL)
- ...

## Failure modes in trajectories  (→ to DETECT & remove)
| failure mode | symptom in D | detector | threshold / note | source |
|---|---|---|---|---|
| answer leakage in CoT | answer stated pre-search | answer_in_cot | τ=0.5 (strong) | [URL] |
| ... | | | | |

## Open intuitions (status)
- "<intuition>" — confirmed? <yes/no/partial> — fix: <...> — [URL]

## Recommended audit command
\`\`\`bash
python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
  --benchmark <preset> --opt ... --out flags.jsonl --aggregate
\`\`\`
```

## Benchmark → preset map
`run_audit.py` ships seed threshold presets (`--benchmark <name>`); tune them
from your score distributions and commit changes back to `BENCHMARK_PRESETS`:

| category | benchmarks | preset key(s) |
|---|---|---|
| Search (deep) | BrowseComp, LiveBrowseComp, K-BrowseComp, DeepSearchQA | `browsecomp`, `livebrowsecomp`, `k-browsecomp`, `deepsearchqa` |
| Search (wide/report) | WideSearch, Ko-WideSearch, DeepResearch, ReportGeneration | `widesearch`, `ko-widesearch`, `deepresearch`, `report-generation` |
| MCP / tools | MCP-mark, MCP-Atlas, Tool-Decathlon | `mcp-mark`, `mcp-atlas`, `tool-decathlon` |
| Long-horizon | DeepPlanning | `deepplanning` |
| Agentic dialog | Tau2, Tau3 | `tau2`, `tau3` |

> Presets are **starting points**, not validated thresholds. Always read the
> score distribution (`--aggregate`) before trusting a flag rate.
