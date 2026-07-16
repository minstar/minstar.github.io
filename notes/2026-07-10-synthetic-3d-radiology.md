# Inventing the z-axis

I spent an afternoon with a radiology MD-PhD and came away with an idea I can't put
down. He reads a 2D image — an X-ray, or one axial slice of a CT/MRI, just x and y —
and then does something I hadn't appreciated: he traces, slice by slice, *where the
abnormality extends along z*, stacks those hand-drawn contours into a 3D model, and
takes **that** into the operating room. The 2D image is what gets shared, released,
and benchmarked. The 3D is what the surgery is actually planned on. So the thing we
kept circling: build the step that makes the 3D — turn the 2D radiology everyone
already has into something you can rotate in a browser.

I read the field and built a prototype the same day. The one sentence I keep coming
back to: **the z-axis is missing data, and every method here is a different — more
or less honest — way of inventing it.**

## Why there's nothing to interpolate

It's worse than "missing." An X-ray pixel is a *line integral* of attenuation along
a ray (Beer–Lambert), so the map from a 3D volume to a 2D radiograph collapses a
whole column of voxels into one number and discards depth order entirely. That makes
2D→3D many-to-one: infinitely many volumes reproduce the exact same picture.
Classical CT only inverts this because it collects hundreds of angular views; from
one or two shots the null space is enormous. Nobody *solves* the inversion — they
regularize it with a learned prior `p(volume)` and return the on-manifold volume that
best explains the pixels. A thick-slice stack is the same story locally: between two
slices 6 mm apart there is genuinely no measurement, and a model fills the gap from a
prior. Two recent surveys map the terrain by
[representation paradigm](https://arxiv.org/abs/2504.11349) (voxel-regression vs.
implicit fields vs. diffusion) and by the
[implicit-neural-representation](https://arxiv.org/abs/2307.16142) view.

## Two regimes, one brutal tradeoff

There are really two problems wearing one name, and the interesting structure is a
prior spectrum inside each — trading *how few 2D inputs you need* against *how much
the model confabulates*.

- **Sparse projections: X-ray → CT.** The generative lineage starts with
  [X2CT-GAN](https://arxiv.org/abs/1905.06902) (CVPR 2019): a 2D encoder → 3D decoder
  pulled toward realistic anatomy by an adversarial prior. It then splits by how the
  prior is expressed — an explicit likelihood via a
  [normalizing flow](https://arxiv.org/abs/2104.04179) (2021), true perspective
  X-ray geometry in [PerX2CT](https://arxiv.org/abs/2303.05297) (ICASSP 2023), and
  now conditional diffusion ([DiffuX2CT](https://arxiv.org/abs/2407.13545), ECCV
  2024; [DX2CT](https://arxiv.org/abs/2409.08850), which even accepts a *single*
  view). The cleanest product wedge is dental: reconstruct 3D tooth/bone from one
  panoramic film and spare the patient CBCT dose
  ([Oral-3D](https://arxiv.org/abs/2003.08413), AAAI 2021).

- **Anisotropic slices → isotropic volume.** This is the regime that maps directly
  onto his workflow — z is 3–7× coarser than in-plane, so the stacked contours come
  out staircased and jagged, which hurts planning and 3D printing. The modern move is
  to treat the stack as sparse samples of a continuous field `f(x,y,z)` and fit a
  coordinate network, so you can resample to *any* isotropic spacing before meshing:
  per-scan INR ([IREM](https://arxiv.org/abs/2106.15097), MICCAI 2021;
  [CuNeRF](https://arxiv.org/abs/2303.16242), ICCV 2023), generalizable feed-forward
  INR ([ArSSR](https://arxiv.org/abs/2110.14476), 2022), and the motion-robust
  slice-to-volume case with an actual acquisition model (PSF, inter-slice motion,
  outlier rejection) in [NeSVoR](https://github.com/daviddmc/NeSVoR) (IEEE TMI 2023),
  which ships as a package — the closest thing to a drop-in engine.

- **Making it fast enough to be interactive.** NeRF's "few images → 3D field" idea
  ports to tomography, but the physics change and that's the crux: instead of a
  view-dependent reflectance field you learn a *view-independent* attenuation field
  with a Beer–Lambert forward model ([MedNeRF](https://arxiv.org/abs/2202.01020)
  2022; [NAF](https://arxiv.org/abs/2209.14540) MICCAI 2022;
  [SAX-NeRF](https://arxiv.org/abs/2311.10959) CVPR 2024). The 2024 wave swaps the
  slow MLP for explicit 3D Gaussians with a CUDA X-ray rasterizer —
  [X-Gaussian](https://arxiv.org/abs/2403.04116) (>70× faster),
  [R2-Gaussian](https://arxiv.org/abs/2405.20693) (rectifies an integration bias so
  the splat equals the true line integral),
  [DIF-Gaussian](https://arxiv.org/abs/2407.01090) (extremely sparse-view CBCT).
  Fast enough that reconstruct-then-render can feel live.

## The web part is the easy part

The UX he actually wants — the thing that "kills the static PDF" — is just a
shareable page you can rotate and scrub. That's solved client-side:
[NiiVue](https://github.com/niivue/niivue) loads NIfTI volumes *and* glTF/STL meshes
in one WebGL2 page with MPR, clip planes, and a z-scrub;
[itk-wasm](https://github.com/InsightSoftwareConsortium/itk-wasm) does DICOM→NIfTI
and HU-windowing in the browser so no PHI ever leaves it;
[Cornerstone3D](https://github.com/cornerstonejs/cornerstone3D) and
[VTK.js](https://github.com/Kitware/vtk-js) are the step-ups. For a bespoke "hero"
object it's just marching-cubes → Draco-glTF → three.js. None of this is the hard
part.

## The hard part: a beautiful reconstruction can be confidently wrong

This is the center of the note, not a footnote. Because the missing depth is filled
by a prior, a population-prior method can **invent a lesion that isn't there, or
erase one that is** — and SSIM/PSNR, which is all these papers report, is blind to
exactly that. A reconstruction can score beautifully while getting the one
clinically decisive voxel wrong. The tradeoff is clean and unforgiving: population
priors (X2CT-GAN … DiffuX2CT) work from a single view but hallucinate most, because
they are literally sampling "what typical anatomy looks like here"; self-supervised
per-scan fits (NAF, SAX-NeRF, R2-Gaussian) carry no population prior and stay
faithful to the measurements — but need *tens* of views and collapse at one or two.
The clinically useful middle — biplanar *and* faithful — is precisely the
underserved regime. And the largest gap in the whole literature: there is **no
validated clinical-fidelity metric.** No standard lesion-preservation score, almost
no prospective reader studies on sparse-view reconstructions, and the per-voxel
uncertainty you *can* get from diffusion posteriors is, so far, uncalibrated to
actual error.

## Where I actually aimed

So I built the honest version first. `medical3d` (in `AgentMercury/Architect`) is the
end-to-end skeleton — 2D in → reconstruct z → segment → marching cubes → GLB →
in-browser three.js viewer with the source 2D slices one scrub away. The
reconstruction step is deliberately the *dumb* baseline (cubic through-plane
interpolation), because I want the seam where a learned prior plugs in to be explicit
and auditable. Two runs verify it end-to-end: a synthetic thorax with a nodule that
only lives in a z-range (20 thick slices → 120 isotropic; the red lesion rendered
*inside* the translucent body), and a real FLAIR MRI thinned to 28 slices and
reconstructed back to 140. Both build in ~2 s and render in a headless browser. Point
it at [LIDC-IDRI](https://www.cancerimagingarchive.net/collection/lidc-idri/) or a
[TotalSegmentator](https://zenodo.org/records/10047292) volume and it's real
pathology.

<details class="figure-toggle" open>
<summary>Figure — the phantom, reconstructed and rendered in-browser (click to collapse)</summary>

![medical3d: a synthetic thorax reconstructed from 20 thick slices to 120 isotropic, the z-localized lesion (red) rendered inside the translucent body, with the source 2D axial slice one scrub away](pictures/2026medical3d.png)

</details>

The design choice I care about is that **safety is a feature, not a disclaimer.**
Every output is watermarked synthetic-not-diagnostic; the 2D evidence is always one
scrub away so a viewer can check the 3D against what it came from; and the
interpolation baseline is auditable ground for measuring where a learned prior *adds*
structure. The obvious next step is the one the field is missing: re-project the
reconstructed volume through a differentiable DRR and surface the disagreement with
the input as a live overlay — a measurement-consistency map — alongside calibrated
per-voxel variance.

## Redefining it — the re-slice *is* the experiment (2026-07-13)

For two months this note quietly assumed I'd bring my own volume. What I was
missing was a *supply* of the 2D everyone already shares, and
[MedPMC](https://arxiv.org/abs/2607.07673) just handed it over: 6.1M PubMed Central
articles parsed into 11M image–caption pairs, **25.6 % of them radiology** (within
that, MRI 31.7 % / CT 23.4 % / X-ray 15.1 %), each paired with the sentence that
names the finding. That is the seed pool I didn't have. But the asterisk is
load-bearing, so I'll say it before anything else: a published figure is a *picture
of a slice*, not the slice — windowed, cropped to 8-bit, arrows burned into the
pixels, the HU scale and slice spacing thrown away. You cannot recover depth from
it, and even a multi-panel figure is disconnected renders at unknown, non-uniform
positions (often mixing axial/coronal/sagittal, modalities, even patients). So
MedPMC is a seed *distribution* plus a caption — never 3D ground truth. The z still
comes from a prior (invented) or from a *paired* real volume (measured). That one
distinction is the whole project.

The scene I keep replaying — lift the 2D, then re-slice it from any angle to see the
abnormality end-on — turns out to be two different operations wearing one sentence,
and the difference between them *is* the honesty axis. On a **real volume**, oblique
and [double-oblique MPR](https://radiopaedia.org/articles/double-oblique-multiplanar-reconstruction)
is a faithful, deterministic viewing transform: a 4×4 reslice matrix and a trilinear
read, the same maneuver a radiologist does by hand to size an aortic annulus
perpendicular to the vessel or cut a cardiac short-axis. Nothing is invented — the
pipeline just *automates the plane the doctor places by hand.* On a **single
figure**, every plane but the original one is the prior talking. Which reframes the
multi-angle re-slice from a UX flourish into the actual experiment: a measured lesion
holds its shape as you swing the plane through it; an invented one wobbles, and the
per-voxel uncertainty spikes exactly where the caption pointed. **Re-slicing a
reconstruction fifty ways is a hallucination test** — and that, not a prettier
surface, is what belongs in the viewer. This is the sharp version of the same worry
from "the hard part": theory says a single view is the *worst* case (the volume lives
in the huge null space of a rank-deficient forward operator, so any structure the
prior hallucinates is by construction consistent with the input and invisible to a
reprojection check —
[TMI 2021](https://pubmed.ncbi.nlm.nih.gov/34813472/)); and the field's own metrics
hide it — the 2026 single-view diffusion reconstructor
[AXON](https://arxiv.org/abs/2603.26509) reports 21.21 dB single-view vs 21.71 dB
biplanar, a ~0.5 dB gap that vastly understates that the *entire* depth axis in the
single-view case is fabricated. No X-ray→CT method yet reports whether a real lesion
survives; SSIM is
[provably decoupled from anatomical content](https://www.nature.com/articles/s41598-024-59731-y).

None of the four ideas underneath this is mine, and saying so is what locates the
contribution. The measured-vs-invented split I keep leaning on was written down as a
theorem in 2021: Bhadra and Anastasio decompose a reconstruction into a *measurement
component* the data pins down and a *null-space component* the prior invents, and
render the latter as a hallucination map — so "the original plane is measured, every
other plane is the prior" is just the interactive, per-plane reading of that
null-space term. Oblique MPR is decades old and automated; single-view 2D→3D has been
a live field since X2CT-GAN; and using multi-view consistency to catch invented
geometry (test-time-augmentation variance as uncertainty; consistency checks that flag
a hallucinated scene) is standard in general vision. So the missing piece isn't a
component — it's the **wiring**: reconstruct 3D from a single *published figure* (not a
volume), turn arbitrary-angle re-slicing into a live read of that null-space term (the
invented plane wobbles and its uncertainty spikes; the measured baseline doesn't), and
always render the invented plane *beside* its measured baseline — seeded at MedPMC
scale. Every part exists; binding them into one interrogation interface plus a
verification protocol is the blank, and it's the whole point.

The premise I opened with was a doctor tracing the abnormality slice by slice. The
redefinition replaces the pencil with the caption: ground the finding-name to the
image for an in-plane (x, y), turn that box into a mask with
[MedSAM](https://arxiv.org/abs/2304.12306), propagate it through the volume with
MedSAM2. Honesty demands the number here too: the best zero-shot radiology phrase
grounding is ~0.54 mIoU and the best fine-tuned ~0.61 on
[MS-CXR](https://arxiv.org/abs/2204.09817), with plain contrastive-CLIP saliency down
at ~0.27 — so ~40 % of the box is wrong even at SOTA, it is chest-X-ray-only gold, and
it gives you x and y but *never z*. The caption localizes in-plane; the depth of the
finding is still invented. So the grounded region is a **hypothesis the viewer must
let you check against the source panel**, not a contour to trust.

None of this is what `medical3d` does yet, and the gap is the plan. Today it seeds
only from volumes (phantom / NIfTI / LIDC CT) and re-slices *axially* — a scrubber
over pre-rendered PNGs behind one horizontal plane. The redefinition needs four
things it doesn't have: a genuine single-image **+ caption** ingest (a lone PNG
through `--png-stack` just extrudes one slice); a real generative **lift** at the
reconstructor seam (today's cubic and INR only interpolate a z that already exists);
an **arbitrary-angle MPR** viewer (ship the intensity volume to the client and sample
oblique planes on the GPU — Cornerstone3D/VTK.js do this out of the box, NiiVue only
as a clip-plane); and a **fabrication-aware** honesty layer (reproject-to-*input*
residual + generative-ensemble variance + the re-slice-consistency map above, because
the leave-slice-out calibration I built assumes measured slices a single figure can't
give). The phased build, the permissive-license path (CC-BY/CC0 MedPMC seeds paired
with LIDC and TotalSegmentator volumes, so there is real ground truth), and the
evaluation are in `AgentMercury/Architect/medical3d/PLAN.md`. The genuine novelty
boundary is narrow and worth stating plainly: single-projection→3D is solved for
*X-ray* projections and text→3D for *clean clinical reports* — nobody lifts a rendered
publication slice, which is adjacent-but-new, and more ill-posed than either.

Note-to-self: this is the same 2D→3D lift the radiologist already does by hand, now
done by a prior — powerful and dangerous for exactly the same reason. His pencil
contour can be wrong too, but a smooth, confident, GPU-rendered surface *looks*
authoritative in a way a pencil line never does. The publishable target isn't a
prettier reconstruction; it's the missing metric — lesion-preservation plus
calibrated uncertainty, surfaced live in the viewer — because until "looks right" can
be told apart from "is right," this stays a planning aid and never a diagnostic one.
