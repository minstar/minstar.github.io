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

Note-to-self: this is the same 2D→3D lift the radiologist already does by hand, now
done by a prior — powerful and dangerous for exactly the same reason. His pencil
contour can be wrong too, but a smooth, confident, GPU-rendered surface *looks*
authoritative in a way a pencil line never does. The publishable target isn't a
prettier reconstruction; it's the missing metric — lesion-preservation plus
calibrated uncertainty, surfaced live in the viewer — because until "looks right" can
be told apart from "is right," this stays a planning aid and never a diagnostic one.
