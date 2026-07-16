# The road you can't do anything about

The other day, walking in Korea, I passed a road that felt genuinely dangerous — the kind
where you think *a lot of accidents must happen here* — and noticed there wasn't a single
CCTV on it. What stuck with me wasn't the road; it was the powerlessness. There is nothing
a pedestrian can *do* with that observation. I could file a photo into the 안전신문고 app
and it would join a nationwide queue of complaints. Structurally, a Korean road earns an
engineering review by logging casualties: the national improvement program picks a spot up
once it records [five accidents in a year (three outside the big metros)](https://www.archives.go.kr/next/newsearch/listSubjectDescription.do?id=006433&sitePage=).
The feedback loop that redesigns dangerous roads runs on people getting hurt.

Here's the irritating part: the *fixing* half of that loop works startlingly well. Korea has
run the accident-hotspot improvement program (교통사고 잦은 곳 개선사업) continuously
[since 1988 — 23,645 spots and 585 corridors so far](https://www.koroad.or.kr/main/content/view/MN03010700.do).
When a site finally gets treated, deaths at that site drop by roughly **half**, cohort after
cohort: [−56.3% for the 2020 cohort](https://www.korea.kr/news/policyNewsView.do?newsId=148912411),
[−52.7% for 2021](https://www.safetynews.co.kr/news/articleView.html?idxno=227271),
[−59.5% for 2022, the latest analysis](https://www.anjunj.com/news/articleView.html?idxno=40241),
with total accidents down ~31–35%. So re-engineering isn't the bottleneck. Throughput is:
roughly 250 sites a year get the treatment, because each one requires KoROAD's regional
engineers to do an artisanal deep-dive — pull three years of accident records, visit, diagnose,
and write a site-specific improvement plan (the 2021 cohort's construction alone ran about
₩42.1B in national+local funds). The question I want to poke at: **can an LLM agent draft
that diagnosis for every hotspot in the country, so the engineers become reviewers instead
of the bottleneck?**

## The pipeline, and why Korea specifically

As I first wrote it down: hotspot → evidence → diagnosis → grounded redesign → validation,
with every arrow an MCP tool call. What makes this concrete in Korea is that the first two
arrows already exist as public APIs, to a degree I don't think any other country matches:

- **Hotspots.** KoROAD publishes accident-frequent-zone data in
  [a dozen flavors](https://opendata.koroad.or.kr/) — pedestrian, bicycle, school-zone,
  drunk-driving, elderly-pedestrian, freight, icy-road, per-municipality TOP-3 — each zone
  carrying a centroid, a micro-polygon (`geom_json`, EPSG:4326), and occurrence/casualty/death
  counts ([per-municipality API](https://www.data.go.kr/data/15057467/openapi.do),
  [bulk standard dataset](https://www.data.go.kr/data/15029185/standard.do)). Several layers
  are themselves defined on rolling three-year windows — the pedestrian layer is 7+
  death-or-serious-injury accidents within a 100 m radius over the last three years. The bulk
  data currently runs through accident-year 2024, so "the last three years" means 2022–2024
  (the 2025 layer should land this fall if the cadence holds). Fatal accidents additionally
  come as per-accident microdata: coordinates, road form, violation type, day/night.
- **Cameras.** The national ITS center exposes
  [live road CCTV by bounding-box query](https://www.data.go.kr/data/15040466/openapi.do) —
  hand it a hotspot's bbox and it returns camera names, coordinates, and live stream URLs for
  expressways and national arteries; the police-run UTIC adds
  [municipal traffic-control cameras](https://www.data.go.kr/data/15148511/openapi.do), open
  since 2016. Beyond the live feeds, a standard register lists
  [353,263 public outdoor CCTVs](https://www.data.go.kr/data/15013094/standard.do) with
  location, purpose (traffic enforcement vs. crime prevention), and heading — locations only.
- **Streets.** Kakao's [roadview API](https://apis.map.kakao.com/web/sample/basicRoadview/)
  hands you the panorama nearest any coordinate — imagery for essentially every road in the
  country, including the ones no camera watches.
- **Standards.** On the countermeasure side, the US
  [CMF Clearinghouse](https://cmfclearinghouse.fhwa.dot.gov/) catalogs 3,000+ crash
  modification factors — study-backed effect sizes per treatment ("install pedestrian refuge
  island: expected crash change −X%") — and Korea has its own traffic-safety-facility manuals
  and the annual improvement-plan reports themselves.

And the observation that makes this a buildable project rather than a grant proposal:
[Kakao](https://github.com/cgoinglove/mcp-server-kakao-map) and
[Naver](https://github.com/yunkee-lee/mcp-naver-maps) map MCP servers already exist, the
[OSM ones](https://github.com/jagan-shanmugam/open-streetmap-mcp) are mature — but as of this
month there is **no accident-data or road-safety MCP server anywhere**, not for TAAS, not
even for NHTSA's FARS beyond an auto-generated API wrapper. The agent layer simply hasn't
touched this domain. Four thin servers — `taas-mcp`, `cctv-mcp`, `roadview-mcp`,
`standards-mcp` — and the evidence loop closes.

## What's already done, so I don't claim someone else's gap

The naive version of the idea — "VLM looks at street imagery and suggests improvements" — is
taken, and recently.
[From Crash Reports to Safer Roads](https://www.sciencedirect.com/science/article/abs/pii/S000145752600028X)
(*Accident Analysis & Prevention*, 2026) runs VLMs over 4,302 Massachusetts crash reports,
attributes each crash to human/vehicle/road/environment factors, aggregates attributions into
hotspots, then reads street-view imagery at the high-risk sites and generates design
recommendations. Around it sits a fast-moving lineage:
[TrafficSafetyGPT](https://arxiv.org/abs/2307.15311) (2023) fine-tunes an LLM on safety
guidebooks; [CrashLLM](https://arxiv.org/abs/2406.10789) (2024) reframes 19,340 crash records
as language and asks what-if; [V-RoAst](https://arxiv.org/abs/2408.10872) (2024) asks whether
a VLM can be an iRAP road-safety assessor from street images;
[SeeUnsafe](https://arxiv.org/abs/2501.10604) (2025) turns traffic-camera accident video into
an MLLM-agent workflow; [UrbanX](https://arxiv.org/abs/2506.02242) (2025) has an MLLM agent
discover which streetscape factors predict crashes. In Korea the adjacent efforts are
institutional, not LLM: KoROAD stood up an
[AI transformation office](https://www.safetimes.co.kr/news/articleView.html?idxno=236995) in
Dec 2025, and Yangju won the 2026 AI-city competition with an
[agentic collision-risk prediction pilot](https://edaily.co.kr/News/Read?mediaCodeNo=257&newsId=06500966645451216)
for residential back-roads.

What no system does yet — verified rather than assumed:

1. **Use live CCTV as evidence.** Everything above reads static street view or curated video
   datasets; nobody composes hotspot statistics with what the road's own cameras show today.
2. **Ground countermeasures in effect sizes.** No published system wires an LLM to the CMF
   Clearinghouse or any national design standard via retrieval — recommendations stay
   fluent-but-unpriced. A [2025 review of LLMs for roadway safety](https://arxiv.org/abs/2506.06301)
   explicitly names RAG-over-manuals as the missing pattern.
3. **Validate proposals in simulation.** [ChatSUMO](https://arxiv.org/abs/2409.09040) (2024)
   and [AgentSUMO](https://arxiv.org/abs/2511.06804) (2025) let LLMs build SUMO scenarios but
   stop at flow metrics; nobody closes LLM-proposes → simulate → score with surrogate safety
   measures ([SSAM-style](https://highways.dot.gov/sites/fhwa.dot.gov/files/FHWA-HRT-08-049.pdf)
   TTC/PET conflict counts, the standard proxy when you can't wait years for crash data).
4. **Expose any of it as MCP tooling** an agent — or a city hall — can compose.

## The eval is the actual idea

Everything above is engineering. The reason I think this is *research* is an evaluation that
Korea uniquely makes possible, and that I haven't seen used anywhere: **the improvement
program publishes its homework.** Every year each KoROAD regional chapter writes a
기본개선계획 — per-site diagnosis and custom countermeasures — and later an 효과분석
comparing the three pre-improvement years against the post-year. That is a historical
hold-out set for exactly this task. Freeze the agent at the engineers' information state:
accident data through year T−1, pre-improvement imagery only. Ask for a diagnosis and ranked
countermeasures. Score against (a) what the engineers actually prescribed, and (b) the
accident delta that actually materialized — worked cases like
[인천 간석동 −58.9% and 부산 부평교차로 −81.8%](https://www.korea.kr/news/policyNewsView.do?newsId=148912411)
are already public. No LLM judge anywhere in the loop; the ground truth is poured concrete
and casualty counts. Agent evals that grade themselves confirm themselves — this one can't.

Two honest complications. First, the reports are
[catalogued in the National Library](https://www.nl.go.kr/NL/contents/N20103000000.do?schM=contList&schOpt1=CA0000000031&schOpt2=CA0000000375&schOpt3=04)
but mostly not downloadable as PDFs — assembling the before/after corpus is real archival
work, or a reason to just call KoROAD (their new AI office makes the timing right). Second,
naive before/after **inflates effects via regression to the mean**: sites are selected
*because* counts spiked, so part of that −59.5% is reversion that would have happened anyway
— the empirical-Bayes correction exists for exactly this, and
[domestic effect analyses](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003151194)
slice effects by improvement type. An agent benchmarked this way must be scored against
corrected deltas, or it learns to take credit for luck.

## Walls

- **The road that started this note isn't in the data.** Hotspot layers require reported
  accidents; open CCTV clusters on expressways and arteries. That alley has neither —
  observability is allocated by past harm, which is precisely the complaint I started with.
  Partial outs: roadview covers nearly every road, so V-RoAst-style *proactive* rating of
  unrated roads is feasible; and commercial-vehicle DTG telemetry (hard-braking events) is a
  real leading indicator, but the
  [full microdata sits behind a secure-zone access regime](https://main.kotsa.or.kr/portal/contents.do?menuCode=03030200)
  — only samples and aggregates are open. The agent should degrade gracefully:
  CCTV → roadview → statistics-only.
- **VLM spatial reasoning is the weak link.** V-RoAst's own result: zero-shot VLMs
  underperform task-specific CNNs on spatially-grounded road attributes. A redesign hinges on
  exactly those — sight distance, curvature, crossing exposure. The agent should reason over
  structured extractions (detectors and segmenters exposed as tools too), not raw pixels alone.
- **Plausible ≠ effective.** An LLM will always produce a fluent countermeasure list; "add a
  signal, repaint the crosswalk" never *sounds* wrong. The CMF grounding and the simulation
  check are both there to convert "sounds right" into "expected −X%, with a citation" — every
  claim in the dossier has to trace to a tool result, not the model's prior.
- **Live-only cameras, license gray zones, privacy.** There is no archived-footage API — you
  see today's geometry and behavior, never the crash itself. Kakao/Naver roadview terms for
  bulk VLM analysis are unresolved. And CCTV frames carry plates and faces, so a blur pass is
  table stakes before anything leaves the pipeline.

## Where I'd actually start

One city, one quarter of effort. Build the four MCP servers thin: `taas-mcp` is a few
endpoints over the hotspot and fatal-accident APIs; `cctv-mcp` is bbox → frames with
blurring; `roadview-mcp` wraps Kakao's nearest-panorama call; `standards-mcp` is retrieval
over the CMF Clearinghouse plus Korean facility manuals. Run the agent over ~50 hotspots in
one district and produce site dossiers: evidence images, diagnosis, ranked countermeasures
with cited effect sizes. Separately — and honestly, first — digitize one region's past
기본개선계획 into 30–50 before/after cases and run the frozen-clock replay. If the agent's
countermeasure sets overlap the engineers' at a useful rate and its effect directions track
the corrected deltas, scale the corpus; if not, the dossiers are still a well-structured
failure dataset. Either way the deliverable that outlives the model generation is the
**benchmark**: Korea is the one place with enough public instrumentation *and* a 37-year
paper trail of ground-truth redesigns to build it.

The road I walked past still has no camera and no file. The point of automating diagnosis on
the instrumented roads is to make diagnosis cheap enough that a roadview panorama and one
citizen report become sufficient input — so that a road no longer has to earn its engineering
review in casualties.
