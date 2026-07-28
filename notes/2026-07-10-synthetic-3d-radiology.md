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

None of that was what `medical3d` did when I wrote this, and the gap was the plan. It
seeded only from volumes (phantom / NIfTI / LIDC CT) and re-sliced *axially* — a
scrubber over pre-rendered PNGs behind one horizontal plane. Four things were missing:
a genuine single-image **+ caption** ingest (a lone PNG through `--png-stack` just
extrudes one slice); a real generative **lift** at the reconstructor seam (cubic and
INR only interpolate a z that already exists); an **arbitrary-angle MPR** viewer (ship
the intensity volume to the client and sample oblique planes on the GPU —
Cornerstone3D/VTK.js do this out of the box, NiiVue only as a clip-plane); and a
**fabrication-aware** honesty layer (reproject-to-*input* residual + generative-ensemble
variance + the re-slice-consistency map above, because the leave-slice-out calibration
I built assumes measured slices a single figure can't give). All four are built now —
what they turned out to measure is the section below. The phased build, the
permissive-license path (CC-BY/CC0 MedPMC seeds paired with LIDC and TotalSegmentator
volumes, so there is real ground truth), and the evaluation are in
`AgentMercury/Architect/medical3d/PLAN.md`. The genuine novelty boundary is narrow and
worth stating plainly: single-projection→3D is solved for *X-ray* projections and
text→3D for *clean clinical reports* — nobody lifts a rendered publication slice, which
is adjacent-but-new, and more ill-posed than either.

## The honesty layer, once it had numbers in it (2026-07-27)

The instrument I wanted most was the cheap one: reproject the lifted volume back onto
the figure it came from and check they agree. It is the only consistency check a real
published figure can support — no ground truth, no held-out slices — and it is
genuinely necessary, because a lift that has drifted off its own input is wrong without
further argument. It is also, once you measure it, **almost powerless**, and measuring
that is worth more than the check.

Every lift anyone would actually ship writes the measured slice back into the volume,
so it reproduces the input **exactly** — residual 0. Vacuous by construction, for the
whole family. To find out whether the residual carries *any* signal I built the control
the check deserves: the same population prior with the measured slice deliberately not
written back, a volume that ignored its own input entirely. And to make a raw error
readable — 0.0148 is small compared to *what*? — I reprojected each lift against a
figure from a different case, so "wrong" has a scale. On that scale, 0 means reproduces
its own input and 1 means no better than an unrelated image, the control lands at
**0.161**. A contrast-matched prior already resembles any thorax slice; ignoring the
input completely buys you 16 % of the way to nonsense. That is the entire dynamic range
of the check the field reaches for first.

Which is exactly the failure the 2021 theorem predicts, now with a number on it:
reprojection probes the measurement component, and every invention lives in the null
space where it cannot look. The dissociation is clean on the same three volumes. The
population-prior lift **erased the tumour** off-plane and passed reprojection at 0. The
null-baseline lift **smeared it** through every slice and passed reprojection at 0. Only
the multi-angle re-slice separated them from the truth — consistency 0.00 and 0.14
against 0.72 — and only a projection through an axis the input never constrained showed
the two lifts differ at all, by 19× (0.152 vs 0.008). *The check that is available is
blind to the thing that matters; the check that catches it needs angles the figure never
gave you.* Both now sit in the viewer side by side, which is the honest way to ship them.

Then the pencil-replacement, measured. I put a served open-weights vision-language model
at the grounder seam and scored it against ground truth on 58 figures rendered from
known volumes — a planted nodule at 24 positions across both lungs plus real LIDC
slices, each rendered twice, with an author's arrow and plain. The first run said "mIoU
0.156" and I could not tell you whether that beat a coin flip. So I split the number:
IoU fuses **localization** (is the predicted centre on the finding) with **scale** (is
the box the right size), and without a floor neither is readable. Against chance — a
correctly-sized box dropped at random — the model is **34× better** at pointing, so it
is doing something real. It also puts its centre **0.78 lesion-diameters** off the
finding and hits IoU 0.5 on 3 % of cases. It finds the *neighbourhood*, not the finding:
a weak hypothesis to check against the source panel, which is what I said grounding
would be, now with the gate failing on the record rather than in a footnote. Upsampling
the figure 4× does not fix it (pointing 0.31 → 0.21), so this is a capability limit, not
a resolution artifact — though it does fix the *box size*, which is precisely why the
two abilities had to be scored apart.

The decomposition also caught me. My own arrow-following baseline was using one image
fraction for two unrelated quantities — how far past the arrowhead the finding sits, and
how big the region around it should be. On a 512-pixel clinical slice that offset
overshot the nodule completely, and its localization on real LIDC data was **zero**.
Keyed to the arrow's own extent and to the anatomy in millimetres instead, the same
baseline goes to perfect pointing and its LIDC overlap sextuples (0.052 → 0.306). A
metric that only reports one fused number cannot tell you which half is broken, and for
two weeks it didn't.

One last thing the survey settled, and it is a licensing result, not a technical one.
Every radiology-specific grounder worth trying has public weights and **not one is
release-compatible**: the phrase-grounding models are non-commercial, the segmentation
foundation model is share-alike copyleft. Under the permissive path this project is
committed to, that leaves the generic vision-language model above as the *only* grounder
that can actually ship — which is why its 0.31 is the number that matters rather than a
better one obtainable internally. The lift seam got the opposite answer:
[DVG-Diffusion](https://arxiv.org/abs/2503.17804), a dual-view X-ray→CT diffusion
reconstructor trained on LIDC-IDRI, is on the Hub under Apache-2.0, 3.8 GB — the same
volumes this repo already ingests. So the trained prior I assumed was out of reach is a
download away — and since it consumes X-ray *projections*, and the
pipeline already renders Beer–Lambert line integrals, it can be fed the input it was
trained for while the published-cross-sectional-figure case stays the harder cousin it
has always been. That is the next thing to build, and the first one where the
lesion-preservation FROC this note has been asking for since July will mean anything.

## The trained prior erases a three-centimetre tumour (2026-07-28)

The reconstructor is in. Two chest radiographs go into a diffusion model trained on
LIDC-IDRI, a 128³ volume comes out in two and a half seconds, and by every structural
measure it is the right patient: body-outline Dice **0.912**, smoothed correlation 0.810
against 0.18 for the same reconstruction compared to a laterally shifted truth. It beats the
single-slice lifts and it beats a no-prior linear back-projection, which is the
comparison that actually asks whether the *learning* buys anything rather than the extra
view. Then I planted nodules of known size in the original 0.88 mm scan, carried them
through the identical path, and asked a matched-filter observer whether they were still
there.

| diameter | signal it puts in the radiographs | detectability retained |
|---:|---:|---:|
| 10 mm | 1.0 % | **−0.23** |
| 16 mm | 2.2 % | **−0.12** |
| 24 mm | 3.2 % | **−0.10** |
| 32 mm | 4.0 % | **0.00** |

Nothing survives. Not the 10 mm nodule, and not one three centimetres across that no
radiologist would miss on the source CT. The same volume that scores 0.91 on body outline
retains zero of the lesion's detectability — which is the sentence this note opened with
in July, now with a trained model, real clinical data, and a task metric instead of a
pixel one behind it.

The middle column is what makes that a finding rather than a bug in my harness, and it
is the first thing I checked. It is the peak change each planted nodule makes in a
radiograph, as a fraction of that view's dynamic range, and it climbs monotonically with
diameter: the information genuinely *is* in the model's input, and the reconstruction is
discarding it. It also sizes the problem honestly, which I find more useful than the
indignation. Even a 32 mm mass perturbs the projection by four percent, and a hundred-step
diffusion prior does not preserve a four-percent perturbation of its conditioning. The
prior is not malfunctioning. It is doing what a prior does when the measurement is weak,
and a lesion is precisely the kind of small, high-contrast, low-prior-probability object
that loses that argument.

Getting an honest number out at all took four metrics, and three of them were wrong in
the same direction — worth writing down, because each looked reasonable. Raw voxel
correlation between reconstruction and truth is **0.10**, which reads as total failure
and nearly made me discard a working model; it is dominated by CT noise, which is exactly
the high-frequency content two views cannot determine and the prior must invent, so it
scores the fabricated part and ignores the recovered one. Mean absolute error rewards a
larger field of view, because a bigger cube is mostly air and air is easy. A lung mask
built by filling the body silently empties when the torso touches the cube face, which is
what happens at precisely the crops I was testing. What survived is body-restricted,
smoothed, and referenced to a shift control so that "looks like a chest" earns nothing.

That control then misbehaved three times as a *selector*, which is the part I'd want a
reviewer to notice. It picked the largest field of view; it made the null-baseline lift
look best because a repeated slice anti-correlates with a shifted chest; and — the one
that matters — when I used it to settle the model's unstated axis convention by sweeping
all forty-eight orientations, its winner had determinant −1. A mirror. A mirrored volume
passes every re-slice test and every reprojection test in this project, because it is
perfectly self-consistent and merely wrong-handed, and a note about hallucination honesty
shipping a chirality bug would be its own punchline. The criterion I'd already switched
to for an unrelated reason is what caught it.

Two more results from the honesty layer, both of which sharpened claims I had been making
loosely. First, provenance: a projection reconstructor has no measured plane at all — the
data constrain line integrals, not voxels — so Bhadra and Anastasio's decomposition has to
be re-derived against the actual forward operator. Two 128×128 detectors constrain at most
2·128²/128³ of the volume, so **every** voxel is at least 98.4 % null-space by rank alone,
and the 16.5 % that no ray reaches is *provably* invented. That is a certificate, not an
estimate, and it is one-sided on purpose: zero ray support proves a voxel is unmeasured
and nonzero support proves nothing.

Second, and this one surprised me: in that certified-unmeasured shell the generative
ensemble's disagreement is **exactly zero**. Not small — zero, with none of the most
disagreeing voxels anywhere inside it. Ensemble variance is the standard empirical stand-in
for null-space uncertainty, and here it is blind to the region that is provably null-space,
because the prior fills that shell with air identically every time. On this case the truth
is air there too, so the invention is correct and unfalsifiable, and I say so rather than
claim a scandal. But the sharper statement holds: **provably-unmeasured is not
visibly-uncertain.** An uncertainty map driven by ensemble spread alone paints the certified
null space confident. That is a true statement about the model and no statement whatsoever
about whether it is right, which is why both signals now ship side by side.

The reprojection residual, finally, is no longer vacuous. Every lift that pastes its input
back reproduces it at exactly zero, so the check said nothing about them; the trained
reconstruction lands at 0.110 on the same scale, against 0.161 for a control that ignored
its input entirely. It has a working range now — and remains the weakest test available,
since the null space is by definition what those two rays cannot see.

The frame I keep coming back to is the arithmetic one. One published cross-sectional
figure determines 0.78 % of a 128³ volume. Two radiographs determine 1.56 %. Every method
in this note, including the trained one, is filling in more than ninety-eight percent from
a prior, and the fidelity numbers describe how *plausibly* it fills it, never how
correctly. The single-figure path — the one the redefinition is actually about — is the
harder cousin of the case measured here, and this is its optimistic bound.

Note-to-self: this is the same 2D→3D lift the radiologist already does by hand, now
done by a prior — powerful and dangerous for exactly the same reason. His pencil
contour can be wrong too, but a smooth, confident, GPU-rendered surface *looks*
authoritative in a way a pencil line never does. The publishable target isn't a
prettier reconstruction; it's the missing metric — lesion-preservation plus
calibrated uncertainty, surfaced live in the viewer — because until "looks right" can
be told apart from "is right," this stays a planning aid and never a diagnostic one.
