# Normalized record schema

Every detector reads **only** the normalized `Record` below — never your raw
JSONL directly. You describe the mapping from your fields to this record once,
in `field_map.yaml`. Detectors then work unchanged across every benchmark.

## Record

| field | type | meaning | used by |
|---|---|---|---|
| `sample_id` | str | stable id (falls back to `row{n}`) | join key for flags |
| `question` | str | the task / prompt | context_bloat |
| `gold_answer` | str? | ground-truth answer | answer_in_cot, unsupported_correct |
| `pred_answer` | str? | model's final answer | correctness fallback |
| `correct` | bool? | is the prediction right? | unsupported_correct, calibration |
| `confidence` | float? | normalized to **[0,1]** | confidence_saturation, calibration |
| `reasoning` | str | full concatenated CoT | (convenience) |
| `steps` | list[Step] | ordered trajectory | all trajectory detectors |

### Step

| field | type | meaning |
|---|---|---|
| `index` | int | position in the trajectory (monotonic) |
| `role` | str | `assistant` \| `tool` \| `user` \| `system` |
| `text` | str | reasoning/content emitted at this step |
| `tool_name` | str? | the called tool, if any |
| `tool_category` | str? | `search` \| `open` \| `find` \| `other` (from `taxonomy`) |
| `tool_query` | str? | the query/argument string of the call |
| `tool_response` | str? | the observation returned to the model |

The `search` / `open` / `find` taxonomy mirrors OpenAI gpt-oss `simple_browser`
(`search`, `open`, `find`) so browsing behavior can be audited per-verb.

## Two ways to express a trajectory

A row maps to `steps` via **one** of these blocks in `field_map.yaml`:

- **`messages:`** — your row has an OpenAI-style `messages[]` array. The loader
  walks it: assistant messages become reasoning steps (and emit one step per
  entry in their `tool_calls`), tool/function messages become tool-response
  steps. This is the common case for chat-formatted trajectories.
- **`tools:`** — your row has a flat list of tool-call objects, each with a
  name / query / response (and optionally a per-call reasoning string).

If neither is present, `steps` is empty and trajectory detectors `skip`.

## Correctness & confidence

- `correct`: read from `correct:` path if given (accepts bool / 0-1 / yes-no /
  correct-incorrect strings). If absent, it is inferred as
  `normalize(gold) == normalize(pred)` **only when both exist** — otherwise it
  stays `None` and correctness-dependent detectors `skip`.
- `confidence`: set `scale:` to map your range onto [0,1] (e.g. `scale: 100`
  for percent). Out-of-range values are clamped.

## Golden rule

A missing field yields **`skipped`**, never a wrong flag. If `skipped` is high,
fix `field_map.yaml` — not the detector. See `field_map.example.yaml`.
