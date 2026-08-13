// Next-paper horizons workflow for /auto-tech-report --horizons.
//
// Reads minstar's own recent papers + his research notes + the frontier tech-report catalog, then
// crosses them from several deliberate angles to propose his NEXT-PAPER directions. Output is a
// PRIVATE deliverable (strategic — do not auto-publish); the caller writes + surfaces it for review.
//
// HOW TO RUN: edit the CONFIG consts below if paths differ, then Workflow({ scriptPath: this }).
// No `args` — everything is inlined or read from disk by the agents (the args channel is unreliable).

export const meta = {
  name: 'auto-tech-report-horizons',
  description: "Read minstar's recent papers + research notes + the tech-report catalog and propose his next-paper directions from new angles, then critique and rank them.",
  phases: [
    { title: 'Gather', detail: 'read authored corpus (last ~2y), research notes, and the frontier catalog' },
    { title: 'Ideate', detail: 'several distinct crossing-angles each propose candidate next papers' },
    { title: 'Rank', detail: 'dedup, critique for novelty/moat-fit/feasibility, rank the survivors' },
  ],
}

// ── CONFIG (edit if paths change) ───────────────────────────────────────────────────────────────
const REPO = '<shared-work>/workspace/minstar/minstar.github.io';
const NOTES_GLOB = `${REPO}/notes`;                              // dated research notes + insights file live here
const INSIGHTS = `${REPO}/notes/insights-tech-reports.md`;      // the frontier tech-report catalog
const CORPUS_STYLE = '<home>/.claude/skills/paper-voice/authored_corpus_style.md'; // his authored-paper corpus table + theses
const IDENTITY_MEMO = '<home>/.claude/projects/-upstg-private-minstar/memory/minstar_identity_scholar.md';
const SCHOLAR = 'https://scholar.google.com/citations?user=jwx0FLoAAAAJ'; // last-2y papers (fetch is best-effort; arXiv fallback)

// The deliberate crossing-angles. Each ideation agent takes ONE. Diversity is the point — an angle
// forces a non-obvious cross between his demonstrated moat and a frontier/notes signal.
const ANGLES = [
  { id: 'verifier-integrity', prompt: "Cross his demonstrated moat in retrieval-GROUNDED factuality + automatic verifiers (OLAPH factuality statements, Self-BioRAG self-reflection, his benchmark-audit work) with the frontier's reward-channel-integrity / anti-Goodhart / grader-awareness findings. What paper does he uniquely get to write about verifiers that cannot be gamed?" },
  { id: 'world-authoring', prompt: "Cross his agentic trajectory / environment data-synthesis work (env-synth/dive-synth as a 'planet' that authors worlds + rubrics) with the frontier's verifiable-environment RL stacks and world-model results. What paper turns environment AUTHORING itself into the contribution?" },
  { id: 'post-cutoff-distill', prompt: "Cross his on-policy / distillation instincts and factuality grounding with the frontier's cross-tokenizer on-policy distillation + post-cutoff knowledge measurement. What paper does the date-gated token-level reward — the one piece with no prior art — become?" },
  { id: 'efficiency-domain', prompt: "Cross his biomedical/domain-expert moat and small-open-model deployment reality with the frontier's on-device efficiency (QAT, KV-cache compression, encoder-free multimodal, energy floor). What paper puts a grounded/factual domain agent on minimal power?" },
  { id: 'over-reflection-rl', prompt: "Cross his over-reflection taxonomy + state-conditioned stop/pivot RL with the frontier's agentic-eval internals (phantom-budget early stops, excessive-answer columns, multi-agent orchestration). What paper makes 'know when to stop searching' a first-class, measurable RL contribution?" },
  { id: 'contrarian', prompt: "Free / contrarian angle: what is EVERYONE (both his notes and the frontier reports) missing or taking for granted that he — given his exact skill set — is unusually positioned to expose or fix? Prefer a sharp, falsifiable claim over a safe extension." },
];

const CORPUS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    trajectory: { type: 'string', description: '3-4 sentences: the arc of his published work and where it is heading (biomedical RAG/factuality -> agentic/search + synthesis + efficiency).' },
    papers: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { title: { type: 'string' }, year: { type: 'string' }, venue: { type: 'string' }, thesis: { type: 'string' }, method: { type: 'string' }, artifact: { type: 'string' } },
      required: ['title', 'year', 'thesis'] }, description: 'His 1st-author / led papers, emphasize the last ~2 years; include any in-progress (OpenBioRQ).' },
    through_lines: { type: 'array', items: { type: 'string' }, description: 'Recurring methods/skills that are his MOAT across papers (e.g. retrieval grounding, automatic factuality verifiers, open-source release discipline, ablation rigor).' },
    fetch_notes: { type: 'string', description: 'What you could/could not fetch (Scholar often blocks scraping; say so).' },
  },
  required: ['trajectory', 'papers', 'through_lines'],
};

const NOTES_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    notes: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { name: { type: 'string' }, thesis: { type: 'string' }, open_question: { type: 'string', description: 'the note\'s own stated "what I\'d check next" / unresolved crux' } },
      required: ['name', 'thesis', 'open_question'] } },
  },
  required: ['notes'],
};

const FRONTIER_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    reports: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { title: { type: 'string' }, org: { type: 'string' }, key_technique: { type: 'string' }, newly_enables: { type: 'string', description: 'the ONE thing this report newly makes possible or newly makes urgent' } },
      required: ['title', 'key_technique', 'newly_enables'] } },
  },
  required: ['reports'],
};

const CANDIDATE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    candidates: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: {
        title: { type: 'string', description: 'a working paper title (specific, not a topic area)' },
        angle: { type: 'string', description: 'the new perspective / non-obvious cross in one sentence' },
        gap: { type: 'string', description: 'the unsolved thing it addresses, grounded in a named frontier report AND/OR a named note' },
        why_positioned: { type: 'string', description: 'why HE specifically can write this — which prior papers/skills are the moat' },
        first_experiment: { type: 'string', description: 'a concrete, cheap, falsifiable FIRST experiment (his "what I\'d check next" style)' },
        bridges: { type: 'array', items: { type: 'string' }, description: 'named notes + named reports it connects' },
        novelty_honesty: { type: 'string', description: 'the honest part: what already exists / what is genuinely new; label a stretch a stretch' },
      },
      required: ['title', 'angle', 'gap', 'why_positioned', 'first_experiment', 'novelty_honesty'] } },
  },
  required: ['candidates'],
};

const HORIZONS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    meta_reflection: { type: 'string', description: '2-4 sentences: the cross-cutting NEW PERSPECTIVE that unifies the strongest candidates — the thing to notice about where his next paper should go.' },
    ranked: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: {
        rank: { type: 'number' }, title: { type: 'string' }, one_liner: { type: 'string' },
        angle: { type: 'string' }, gap: { type: 'string' }, why_positioned: { type: 'string' },
        first_experiment: { type: 'string' }, bridges: { type: 'array', items: { type: 'string' } },
        novelty_honesty: { type: 'string' }, risk: { type: 'string', description: 'the main reason it could fail or be un-novel' },
        scores: { type: 'object', additionalProperties: false, properties: {
          novelty: { type: 'number' }, moat_fit: { type: 'number' }, feasibility: { type: 'number' }, timeliness: { type: 'number' } },
          required: ['novelty', 'moat_fit', 'feasibility', 'timeliness'], description: 'each 1-5' },
      },
      required: ['rank', 'title', 'one_liner', 'angle', 'gap', 'why_positioned', 'first_experiment', 'novelty_honesty', 'risk', 'scores'] } },
  },
  required: ['meta_reflection', 'ranked'],
};

// ── Phase 1: Gather (barrier — every ideation angle needs the full picture) ──────────────────────
phase('Gather');
const [corpus, notesData, frontier] = await parallel([
  () => agent(
    `Assemble minstar's (Minbyul Jeong) AUTHORED research corpus, emphasizing the last ~2 years, for a next-paper brainstorm.
Read these local files with the Read tool:
- ${CORPUS_STYLE}  (his authored-paper corpus table: titles, years, venues, theses, methods)
- ${IDENTITY_MEMO}  (his identity + led papers)
Then BEST-EFFORT fetch his latest work (Scholar often blocks scraping — if it fails, say so and rely on the files + your knowledge of arXiv):
- WebFetch ${SCHOLAR}
- If that yields nothing, WebSearch "Minbyul Jeong" arxiv 2025 2026 for recent 1st-author papers.
Return his led papers (title/year/venue/thesis/method/artifact), a 3-4 sentence trajectory of where his work is heading, and the recurring skills that are his MOAT (retrieval grounding, automatic factuality verifiers, benchmark auditing, open-source release discipline, ablation rigor, agentic data synthesis). Do NOT invent papers; mark uncertainty in fetch_notes.`,
    { label: 'gather:corpus', phase: 'Gather', schema: CORPUS_SCHEMA, agentType: 'general-purpose' }),
  () => agent(
    `Read every research note in ${NOTES_GLOB}/ EXCEPT insights-tech-reports.md (use Glob/Bash to list *.md, then Read each). These are minstar's live research notes. For each, return {name, thesis (1 sentence), open_question (its own stated "what I'd check next" or unresolved crux)}. Be faithful to what each note actually says.`,
    { label: 'gather:notes', phase: 'Gather', schema: NOTES_SCHEMA, agentType: 'general-purpose' }),
  () => agent(
    `Read the frontier tech-report catalog at ${INSIGHTS} (Read the whole file). For each report entry, return {title, org, key_technique (the load-bearing method/result), newly_enables (the ONE thing it newly makes possible or newly makes urgent for a researcher in agentic search/RL/distillation/efficiency)}. Faithful to the entries.`,
    { label: 'gather:frontier', phase: 'Gather', schema: FRONTIER_SCHEMA, agentType: 'general-purpose' }),
]);

const brief = JSON.stringify({ corpus, notes: notesData, frontier }, null, 1);
log(`gathered: ${corpus?.papers?.length || 0} papers, ${notesData?.notes?.length || 0} notes, ${frontier?.reports?.length || 0} reports`);

// ── Phase 2: Ideate (parallel — one distinct crossing-angle each) ────────────────────────────────
phase('Ideate');
const ideas = await parallel(ANGLES.map((a) => () => agent(
  `You are proposing minstar's NEXT PAPER from ONE deliberate angle. Here is the full brief — his corpus + moat, his live research notes (with their open questions), and the frontier tech-report catalog:

${brief}

YOUR ANGLE (${a.id}): ${a.prompt}

Propose 1-2 candidate next papers FROM THIS ANGLE ONLY. Each must: name a specific working title; state the new-perspective cross in one sentence; ground the gap in a NAMED frontier report and/or a NAMED note; say why HE specifically (which prior papers/skills) is positioned to write it; give a concrete, cheap, falsifiable FIRST experiment; and include an honest novelty line (what already exists vs what is genuinely new — do not oversell; a stretch is a stretch). Prefer one sharp idea over two vague ones. Never frame any model as his teacher/judge/base.`,
  { label: `ideate:${a.id}`, phase: 'Ideate', schema: CANDIDATE_SCHEMA, agentType: 'general-purpose' })));

const allCandidates = ideas.filter(Boolean).flatMap((r) => (r.candidates || []).map((c) => ({ ...c })));
log(`ideated: ${allCandidates.length} raw candidates from ${ANGLES.length} angles`);

// ── Phase 3: Rank + synthesize (one judge, higher effort) ────────────────────────────────────────
phase('Rank');
const horizons = await agent(
  `You are the research-direction critic for minstar. Below are candidate next-paper ideas generated from several angles, plus the brief they were generated against.

CANDIDATES:
${JSON.stringify(allCandidates, null, 1)}

BRIEF (his corpus + moat, notes + open questions, frontier catalog):
${brief}

Do the following:
1. DEDUP near-duplicates (merge into the strongest phrasing).
2. Score each survivor 1-5 on: novelty (is it genuinely NOT already covered by his existing notes/papers?), moat_fit (does it leverage skills he demonstrably has?), feasibility (is the first experiment cheap and falsifiable?), timeliness (does a frontier report make it newly possible/urgent NOW?).
3. RANK and keep the top 3-5. Ruthlessly drop anything that is just a restatement of an existing note (those are already his plan, not a NEW perspective) or that he is not positioned to win.
4. For each kept idea, write a tight one_liner, keep angle/gap/why_positioned/first_experiment/bridges/novelty_honesty, and add the single biggest RISK (why it might fail or already be done).
5. Write a meta_reflection: the cross-cutting NEW PERSPECTIVE that the strongest candidates share — the thing to notice about where his next paper should actually go.
Be honest and specific. Never frame any model as his teacher/judge/base/internal dependency.`,
  { label: 'rank:synthesize', phase: 'Rank', schema: HORIZONS_SCHEMA, agentType: 'general-purpose', effort: 'high' });

log(`ranked: ${horizons?.ranked?.length || 0} next-paper directions`);
return { horizons, corpus, notes: notesData, frontier, raw_candidates: allCandidates };
