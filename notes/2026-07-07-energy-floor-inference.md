# The energy floor of inference

Assume we always have *some* power — never zero, but sometimes almost nothing.
Today every model sits on a GPU behind an API sized for throughput. I want to ask
the question from the other end: under an extremely small power budget, can you
quantize an existing model down until it still runs at all — and how far does a
quantized model stretch on the *minimum* power you can give it?

The first thing I had to do was separate two quantities that keep getting fused:
**energy per token** versus **minimum sustained power**. They are not the same
question, and only one of them is actually open.

## Energy per token is already mapped

A cloud query lands around 0.24–0.34 Wh — Google's per-prompt
[disclosure](https://arxiv.org/abs/2508.15734) says a median Gemini text prompt is
0.24 Wh, Altman quoted ~0.34 Wh for ChatGPT, and Epoch AI's independent
reconstruction (~0.3 Wh) put a stake through the old "3 Wh/query" figure as ~10×
too high. Per token that's roughly 0.3–2 J. On the small end,
[MobileLLM](https://arxiv.org/abs/2402.14905) reports a 350M 8-bit model at
~0.035 J/token — enough for all-day conversation on a phone battery. This axis is
well-characterized.

## Quantization is a real lever — but smaller than the headline

The famous number is BitNet b1.58's **71.4× arithmetic-energy** reduction vs FP16
([paper](https://arxiv.org/abs/2402.17764)) — but that's operation-count × per-op
energy, not wall power. Measured end-to-end on CPU
([bitnet.cpp](https://arxiv.org/abs/2410.16144)) the saving is 55–82%, i.e. ~2–6×,
and the [2B4T report](https://arxiv.org/abs/2504.12285) shows 6–12× at ~0.028 J/token
versus FP baselines. The gap between 71× and ~6× is the whole point: **decode is
memory-bound**, so the real mechanism isn't cheaper multiplies — it's a smaller
resident weight footprint and less DRAM traffic.

That reframing changes the question. At extremely low power the binding constraint
isn't arithmetic precision, it's the **idle/static floor**. Energy-proportional
computing (Barroso & Hölzle, 2007) noted a server idles at ~half its peak power; at
low utilization you mostly pay just to keep the chip and the weights powered.
Quantization helps *there* too, but indirectly — by shrinking resident weights into
a lower-power memory tier. That's the lever on the floor, and it's the one nobody
has cleanly isolated for LLMs.

## Anchors for a "how far on minimum power" curve

- **~5 W, interactive:** a ternary edge-FPGA accelerator ([TeLLMe](https://arxiv.org/abs/2504.16266))
  sustains ~25 tok/s.
- **~13 W for a 1B model:** a [MatMul-free LM](https://arxiv.org/abs/2406.02528) on
  a custom FPGA, marketed as a "brain-power budget."
- **~0.035 J/token, all-day on a phone:** MobileLLM's 350M.
- **Below that:** TinyML runs at <1 mW — but on tiny nets, not LLMs. And batteryless
  / energy-harvested *LLM* inference essentially doesn't exist; the intermittent-
  computing literature stops at small networks, where the obstacle is forward
  progress across power failures, not precision.

The floor that doesn't bind is the thermodynamic one: Landauer's kT·ln2 ≈
2.9×10⁻²¹ J/bit means a ~1 J token sits ~20 orders of magnitude above the physical
limit. Useful for rhetoric, useless as a constraint — the real floors are leakage,
memory movement, and idle power.

## The open part

The field has measured energy-per-token to death and shown quantization helps. The
version of the question that's actually novel is the **power-vs-throughput floor**:
the minimum watts to keep a useful quantized model answering at ≥1 tok/s, where the
limiting terms are static/idle power and decode memory bandwidth — neither of which
quantization's *arithmetic* savings touches directly. The sharp experiment isn't
"re-derive J/token by precision," it's: does quantization lower the **floor power**,
and by how much, most plausibly by dropping the resident weights into a lower-power
memory tier? And the hardest, least-claimed case sits at the very bottom —
intermittent, harvested-power inference, where "how far can it run" stops being about
watts and becomes about making forward progress at all.
