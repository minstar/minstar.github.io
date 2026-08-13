# sources.md — where OTHER people's analyses/hypotheses live

Workflow C harvests external claims about these benchmarks (failure modes, data
levers, search/calibration behavior) and logs them in `hypotheses.md`. This file
is the **source registry**: where to look, and the seed URLs to start from.

## Source types (in priority order)
1. **Frontier model system cards / technical reports** — the agentic-eval and
   tool-use sections report failure modes and (sometimes) data-construction
   levers the lab attributes gains to. Highest signal.
2. **The benchmark's own paper** — defines the metric and known contamination /
   answer-format pitfalls.
3. **Papers citing the benchmark** — contamination, leakage, calibration,
   search-behavior, RL-data studies. Search Semantic Scholar / arXiv listings /
   Google Scholar "cited by".
4. **Lab paper collections / model orgs** — HF collections and org pages bundle
   the latest agent/search/RL reports before they're widely indexed.

## Seed URLs (provided 2026-06-30 — starting points, not exhaustive)
| # | URL | type | likely informs |
|---|---|---|---|
| S1 | https://www-cdn.anthropic.com/0f0c97ad20d8005706296bd92aa1c27c6b2f4f61/Claude%20Opus%204.8%20System%20Card.pdf | system card | agentic search, tool-use, calibration, over-search |
| S2 | https://arxiv.org/pdf/2602.15763 | paper | TBD — classify on harvest |
| S3 | https://huggingface.co/collections/Presidentlin/deepseek-papers | collection | DeepSeek agentic/search/RL data findings |
| S4 | https://huggingface.co/Qwen | model org | Qwen3.5 agent/tool-use technical reports |
| S5 | https://arxiv.org/pdf/2602.02276 | paper | Kimi K2.5 (Moonshot) — RL reward/orchestration levers |
| S6 | https://deploymentsafety.openai.com/gpt-5-5/gpt-5-5.pdf | system card | GPT-5.5 — agentic, calibration, hallucination/tool-use |
| S7 | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Pro-Model-Card.pdf | model card | Gemini 3.1 Pro — agentic/tool-use (cards often thin on data) |
| S8 | https://www-cdn.anthropic.com/08ab9158070959f88f296514c21b7facce6f52bc.pdf | TBD | classify on harvest |
| S9 | https://arxiv.org/pdf/2601.03267 | paper | TBD — classify on harvest |

Harvested 2026-06-30 — **13 sources**. Reports/cards: S1=Opus 4.8 card, S2=GLM-5(2602.15763),
S3=DeepSeek(V3.2 2512.02556/R1 2501.12948/Math-V2 2511.22570), S4=Qwen·Tongyi-DR(2510.24701)·
WebSailor(2507.02592)·WebShaper(2509.00375), S5=Kimi-K2.5(2602.02276), S6=GPT-5.5 card,
S7=Gemini-3.1-Pro card, S8=Claude-Mythos-Preview card, S9=GPT-5 card(2601.03267).
Benchmark papers (batch 3): MCP-Atlas(2602.00933), MCPMark(2509.24002), Toolathlon(2510.25726),
WideSearch(2508.07999), DeepSearchQA(2601.20975), DeepResearch-Bench(2506.11763),
ResearchQA(2509.00496), DeepPlanning(2601.18137), Consulting-DR(2605.17554),
τ-bench(2406.12045), τ²-bench(2506.07982), τ-Knowledge(2603.04370), gpt-oss simple_browser.
See hypotheses.md (H-01..H-50).

**Harvest hygiene** (observed): several PDF/HF fetches returned only metadata and the fetch
summarizer HALLUCINATED content (fake arxiv ids, invented failure taxonomies) — agents
discarded these and fell back to HTML / `pdftotext` / source code, tagging residual claims
"secondhand". Always require grounded-vs-secondhand tagging + Q/P quotation from a harvest agent.

## Standing discovery queries (re-run periodically)
- `<model> system card agentic tool use browsing` (each new frontier release)
- `<benchmark> contamination` / `<benchmark> answer leakage` / `<benchmark> calibration`
- `agent trajectory SFT data quality filtering` / `tool-use rejection sampling`
- `deep research over-search redundant query diversity`
- `LLM confidence calibration ECE tool use` / `verifier reward hacking trajectory`
- arXiv listing: search the benchmark name; sort by recency; scan abstracts for
  data-quality / failure-mode language.

## How to harvest (one source → structured rows)
For each source, extract claims of the form *(benchmark, claim about data/behavior,
evidence, proposed fix)* and append them to `hypotheses.md` with the citation.
Map each claim to an existing detector (+ threshold guidance) or flag a NEW
detector to add via Workflow B. **Distinguish quotation from inference** — record
what the source actually says, then your interpretation separately.

Fan-out recipe (keeps main context clean — one focused subagent per source):
> "Read <URL>. Extract every claim about agentic-benchmark **data quality,
> trajectory failure modes, search behavior, or confidence calibration**. For
> each: benchmark, verbatim claim, evidence/numbers, proposed fix, and which of
> {answer_in_cot, unsupported_correct, search_volume, query_redundancy,
> context_bloat, confidence_saturation, step_count, redundant_browsing} it maps
> to (or 'NEW: <name>'). Return structured rows + citation URLs only."
