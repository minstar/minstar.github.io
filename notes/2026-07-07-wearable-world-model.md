# Quantizing a world model onto a wearable

Start from a premise about who owns what. Most people don't have a GPU, but almost
everyone will soon own a wearable with a little NPU in it — glasses, a watch, an
earbud. So the question that interests me isn't "how do we serve a big model," it's
the inverse: can you take a **world model** — a model that predicts how an
environment evolves, that *simulates* — quantize it, compress its cache, and fit it
onto a single device you actually bought? The pipeline as I first wrote it down:
**KV-cache compression + quantization → wearable-class silicon.**

## The parts that already work

The LLM version of this pipeline is not hypothetical — it's shipped.

- **KV-cache compression is mature and stackable.** 2-bit KV cache with near-zero
  quality loss and ~2.6× memory reduction ([KIVI](https://arxiv.org/abs/2402.02750)),
  sub-4-bit with <0.1 perplexity hit ([KVQuant](https://arxiv.org/abs/2401.18079)),
  and architectural [MLA](https://arxiv.org/abs/2412.19437) (DeepSeek-V3) that cuts
  the cache to single-digit percent of dense attention.
- **Low-bit quantization is a near-solved default.** 4-bit weight-only is
  roughly lossless (AWQ/GPTQ); 2-bit needs quantization-aware training but works
  ([BitNet b1.58 2B4T](https://arxiv.org/abs/2504.12285),
  [SpinQuant](https://arxiv.org/abs/2405.16406),
  [ParetoQ](https://arxiv.org/abs/2502.02631)).
- **On a phone, the whole combo already runs.** The
  [Apple Intelligence Foundation Models report](https://arxiv.org/abs/2507.13575)
  literally combines KV-cache sharing with 2-bit QAT — a ~3B model in ~2 GB at
  30 tok/s. [Phi-3-mini](https://arxiv.org/abs/2404.14219) is 4-bit in 1.8 GB;
  [MobileLLM](https://arxiv.org/abs/2402.14905) hits 0.035 J/token, all-day use.

So the compression toolkit is real. The trouble is the two words on either end of
the pipeline: *wearable*, and *world model*.

## Two walls

**Phone ≠ wearable.** The models above run on a *phone* NPU. Real glasses don't do
this. Ray-Ban Meta offloads to a phone and the cloud; Meta's Orion runs only
perception on-glass (hand/eye tracking, SLAM) and pushes the app logic to a wireless
compute puck — and even that needed a ~100× power cut. What actually runs *on the
glass* is TinyML: sub-milliwatt, 32–512 KB of SRAM, keyword-spotting scale
([survey](https://arxiv.org/abs/2506.18927)). Phone-class to glass-class is a 4–6
order-of-magnitude gulf, and no single compression trick closes it.

**"World model" and "KV-cache compression" don't cleanly weld.** KV-cache
compression is an *autoregressive-transformer* optimization. But the world models
you'd actually want either have no KV cache to compress —
[V-JEPA 2](https://arxiv.org/abs/2506.09985) is a latent-space *encoder* that
predicts representations, not tokens — or they're bottlenecked by diffusion sampling
and pixel decoding rather than cache memory (Genie, Matrix-Game). And edge-quantized
world models basically don't exist yet: the deployment floor for a real-time
generative world model today is a single H100. Two recent embodied-world-model
surveys file "quantize/prune the world model" under *future work*.

## Where I'd actually aim

The one credible bridge is the latent encoder. [V-JEPA 2](https://arxiv.org/abs/2506.09985)
is ~1.2B, non-generative, no autoregressive cache — small enough to plausibly
quantize toward phone/NPU class, and nobody has published a quantized or edge variant.
That's a real, fillable gap. But I have to be honest about what it is: that's a
**quantization + distillation** story, and the KV-cache half of my original pipeline
mostly falls away (there's no cache to compress on an encoder). The KV-cache framing
only survives if the world model is an autoregressive *frame* predictor — and those
are exactly the ones whose floor is still a datacenter GPU.

So the note-to-self is that the pipeline has a definitional fork I have to pick
before it even makes sense. Either (a) shrink "world model" down to a latent-dynamics
predictor a wearable can host — and drop the KV-cache half — or (b) keep a generative
world model and accept that this hardware generation it offloads off-device, exactly
like Orion already does. The honest, publishable target is (a): quantize and distill
a V-JEPA-class latent encoder down to NPU class and measure where dynamics-prediction
quality falls off a cliff. That's a paper. "KV-cache your way onto glasses" is, for
now, a category error I talked myself into.
