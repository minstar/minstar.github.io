// Reusable fetch -> independently-verify workflow for /auto-tech-report.
//
// HOW TO RUN (robust pattern): COPY this file to a scratch path, EDIT the SOURCES and LENS consts
// below (inline the run's sources + a fresh ASCII lens built from notes/*.md), then invoke:
//   Workflow({ scriptPath: "<scratch copy>.js" })            // no args — bulletproof
//
// The Workflow `args` channel has repeatedly CRASHED at JSON.parse on the nested {sources, lens}
// payload before any agent runs, so inlining is the default. `args` is still accepted as a
// best-effort OVERRIDE (wrapped so it can never crash the run), but do not rely on it.
//   args.sources : [{ id: string, url: string, hint?: string }]   (1..N sources)
//   args.lens    : string  — "who this is for + which notes to connect to", built fresh each run.
// Returns: [{ src_id, url, summary, verify }]  — read summary + independent verification per source.
// Publishing (apply corrections, write the <details> entry, dedup, commit/push) is done by the caller.

export const meta = {
  name: 'auto-tech-report-fetch-verify',
  description: 'Fetch each tech report / system card, summarize it in detail through a given lens, then independently fact-check every claim before it is published.',
  phases: [
    { title: 'Read', detail: 'fetch each source; summarize (what to read / connections to my notes)' },
    { title: 'Verify', detail: 're-fetch each source and fact-check the summary' },
  ],
}

// ── EDIT THESE PER RUN (inline is the reliable path; keep the lens PURE ASCII) ──────────────────
let SOURCES = [
  // { id: 'shortid', url: 'https://arxiv.org/abs/NNNN.NNNNN', hint: 'arXiv paper - fetch abs + html; sections/numbers to cover...' },
];
let LENS = 'A search/agent researcher doing SFT/RL, agent-trajectory data synthesis, on-policy distillation, reward/verifier design, and agentic/search evaluation. Connect each source to their ongoing research notes by mechanism. Never frame any model as the researcher teacher/judge/base/internal dependency.';

// Best-effort args override — MUST NOT crash the run if the payload is malformed (see header note).
try {
  const A = (typeof args === 'string') ? (args.trim() ? JSON.parse(args) : {}) : (args || {});
  if (Array.isArray(A.sources) && A.sources.length) SOURCES = A.sources;
  if (typeof A.lens === 'string' && A.lens.trim()) LENS = A.lens;
} catch (e) {
  log(`args ignored (parse failed: ${e && e.message}); using inlined SOURCES/LENS`);
}
if (!SOURCES.length) throw new Error('fetch_verify.workflow: SOURCES is empty — inline sources in the script (preferred) or pass args={sources:[{id,url,hint}], lens}.');

const READ_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    url: { type: 'string' },
    title: { type: 'string', description: 'EXACT printed title. If you could not read it, prefix "(UNVERIFIED)".' },
    org: { type: 'string' }, date: { type: 'string', description: 'release date, month+year minimum' },
    source_type: { type: 'string', description: 'system card | technical report | research paper | other' },
    what_it_is: { type: 'string', description: '2-3 plain, NEUTRAL sentences: what the artifact is, its scale/scope (params, pages, dataset size), and its headline claim. No "my teacher / the model I use" framing.' },
    excerpts: { type: 'array', minItems: 5, items: { type: 'string' }, description: "5-8 of the report's OWN load-bearing findings/numbers, each with a section ref (e.g. 'BrowseComp 84.3% single -> 88.5% multi-agent - §8.11'). COVER THE SPREAD: (a) the core method/architecture, (b) the training recipe (data scale, distillation, RL/post-training), (c) 2-3 headline numbers, (d) the eval setup/harness detail, (e) at least ONE caveat/limitation the report itself states. These become the 'From the report' block; they are the source's facts, not opinion." },
    key_facts: { type: 'array', items: { type: 'string' }, description: 'other concrete facts/numbers ACTUALLY stated in the source (superset of excerpts)' },
    read_from_my_view: { type: 'array', minItems: 2, items: { type: 'string' }, description: "2-4 tight bullets: the reader's THOUGHT on which excerpts/sections to read and WHY, at the mechanism level (first person, never generic praise)" },
    connections: { type: 'array', minItems: 2, items: { type: 'string' }, description: '2-4 tight bullets, one per research note it touches: name the note and give a mechanism-level connection; label a stretch a stretch' },
    worth_stealing: { type: 'array', items: { type: 'string' }, description: '0-2 bullets (first person): a concrete technique/number I would port into my own work, or a sharp open question the report leaves unanswered. Optional; omit if nothing rises above the connections.' },
    uncertain: { type: 'array', items: { type: 'string' } },
    fetch_ok: { type: 'boolean', description: 'true ONLY if you actually read the rendered source content' },
  },
  required: ['url', 'title', 'org', 'date', 'source_type', 'what_it_is', 'excerpts', 'key_facts', 'read_from_my_view', 'connections', 'fetch_ok'],
};

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    url: { type: 'string' },
    verdict: { type: 'string', enum: ['accurate', 'minor_issues', 'major_issues', 'could_not_fetch'] },
    confirmed_title: { type: 'string' }, confirmed_org: { type: 'string' }, confirmed_date: { type: 'string' },
    corrections: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { claim: { type: 'string' }, issue: { type: 'string' }, fix: { type: 'string' } },
      required: ['claim', 'issue', 'fix'] } },
    leak_flags: { type: 'array', items: { type: 'string' }, description: 'confidentiality leaks: any phrase framing a model as the researcher\'s teacher/judge/base/internal dependency, or a private infra codename, that must be scrubbed before publishing' },
    notes: { type: 'string' },
  },
  required: ['url', 'verdict', 'confirmed_title', 'confirmed_org', 'confirmed_date', 'corrections', 'leak_flags'],
};

function readPrompt(src) {
  return `You are cataloguing ONE technical report / system card for a researcher's public research-notes page. Fetch the SOURCE and produce a precise, two-dimension summary. Output is schema-validated JSON.

SOURCE: ${src.url}
HINT: ${src.hint || '(none)'}

FETCH RIGOROUSLY (this is published on a public academic site — never invent anything):
- WORK IN A PRIVATE DIRECTORY. Other agents run concurrently. Before fetching anything, create your own directory and put EVERY downloaded file in it under a unique prefix, e.g. WORKDIR=<scratch>/src_${src.id}_read and files like $WORKDIR/${src.id}_abs.html, $WORKDIR/${src.id}.pdf. NEVER write to a shared generic path (/tmp/tr.pdf, p1.pdf, abs1.html) — cached files at generic names have been observed silently REPLACED in place with a different paper mid-session, keeping their original mtime.
- CHECKSUM AROUND EVERY EXTRACTION. Record md5sum of each downloaded artifact immediately after download, and re-check it immediately BEFORE and AFTER every extraction (pdftotext / pdftoppm / Read). If a hash ever changes, discard everything derived from that file, re-download into a fresh path, and redo the extraction. Note this is a DIFFERENT failure from a bad network response: fetching twice and diffing compares responses, not the file still sitting on disk.
- arXiv: WebFetch the abstract page for exact title/authors/date/abstract; then fetch the HTML full text (https://arxiv.org/html/<id>) AND the pdf for intro, method, headline numbers. The HTTP path has been seen silently serving a DIFFERENT paper, so confirm the title you get back matches the id you asked for; if it does not, re-fetch until two fetches agree.
- THE HTML IS A READING AID; THE PDF IS THE SOURCE OF RECORD. Fetching only /html/ has repeatedly produced wrong entries, because LaTeXML silently (a) DROPS the whole author/affiliation block (an empty ltx_authors div on a paper whose PDF cover prints the affiliation under the author line), (b) mis-resolves cross-references (in-text "Table 4" actually pointing at Tables 2 and 3; "Figure 3" at Figure 2), (c) DOUBLES DIGITS in math mode ("6-8 steps" rendering as "66-88", "3-6 on a 1-6 scale" as "33-66 on a 11-66 scale"), and (d) leaves figures as alt="Refer to caption" images whose per-cell values ARE recoverable from the PDF via pdftotext -layout. So: read the HTML for prose, but take every NUMBER, AFFILIATION and table/figure reference from the PDF (rasterize the cover with pdftoppm and read the text layer with pdftotext -layout). Never state a NEGATIVE claim - "no affiliation is given", "the cross-reference is broken", "this value appears nowhere in the paper" - on the strength of the HTML alone; check the PDF first, and if the two disagree, report the PDF and say the HTML rendering differs.
- PDF URL (system cards, etc.): WebFetch the PDF URL. If WebFetch returns nothing usable: Bash \`curl -sL "<url>" -o "$WORKDIR/${src.id}.pdf"\` then Read that path (use the pages parameter).
- If you cannot read the source, set fetch_ok=false, prefix title with "(UNVERIFIED)", explain in uncertain. NEVER fabricate a title, authors, dates, numbers, or findings.
- THE HINT IS A LEAD, NOT A FACT. Any number, spec or claim in the HINT came from web search and has been wrong before (a model card's "500K context" and "Feb 1 cutoff" appeared in no version of the actual card). Check every hint claim against the fetched source and report what the source does and does not contain; put contradicted hint claims in \`uncertain\`. Never carry a hint number into an excerpt because the hint asserted it.
- DO NOT report agent/tooling process detail anywhere in the output. Scratch paths, file overwrites, retry mechanics and directory collisions are internal state; a reader of the public catalog cannot use them and they read as doubt about the entry. Report only properties of the SOURCE.

THE LENS (who this is for, and the notes to connect to):
${LENS}

CONFIDENTIALITY (hard rule): this is published publicly. NEVER frame any model as the researcher's
teacher, judge, base, or internal training/eval dependency (e.g. do NOT write "the teacher I lean on"
or "the model I use to synthesize data/grade evals"), and never name private infra/method codenames.
If a source is a model he uses internally, treat it as a neutral external report and connect it by
MECHANISM only. Keep what_it_is and every bullet leak-free.

BE THOROUGH, NOT THIN. The goal is a detailed catalog entry, so mine the source for the concrete
substance a researcher would want — the actual method, the actual numbers, the actual eval setup, and
the caveats the report admits — not a two-line gloss.

PRODUCE (all grounded in the fetched text):
- title, org, date, source_type, what_it_is (2-3 neutral sentences: what it is + scale/scope + headline claim).
- excerpts: 5-8 of the REPORT'S OWN load-bearing findings/numbers, each with a section ref — the raw
  material for a "From the report" quote block. Report content only, not opinion. COVER THE SPREAD:
  (a) core method/architecture, (b) training recipe (data scale, distillation, RL/post-training),
  (c) 2-3 headline numbers, (d) eval setup/harness detail, (e) at least ONE caveat/limitation the
  report itself states. Prefer a precise number + its context over a vague sentence.
- key_facts: other concrete facts/numbers actually stated (may overlap excerpts).
- read_from_my_view: 2-4 bullets — the researcher's THOUGHT on which excerpts/sections to read and
  WHY, at the mechanism level (concrete, first person, never generic praise).
- connections: 2-4 bullets, one per touched research note — name the note and give a mechanism-level
  link; only claim a connection the source supports; say "stretch" if it is one.
- worth_stealing: 0-2 bullets — a concrete technique/number I'd port into my own work, or a sharp
  open question the report leaves. Omit if nothing rises above the connections.
- uncertain; fetch_ok. One sentence per bullet.`;
}

function verifyPrompt(src, summary) {
  return `You are fact-checking a catalog entry BEFORE it is published on a public research page. INDEPENDENTLY fetch the source and check the entry against it. Do not trust the entry.

SOURCE: ${src.url}
HINT: ${src.hint || '(none)'}
ENTRY TO CHECK (JSON):
${JSON.stringify(summary, null, 2)}

Fetch the source yourself, INTO YOUR OWN PRIVATE DIRECTORY under a unique prefix (e.g. <scratch>/src_${src.id}_verify/${src.id}_*.pdf). Never reuse a shared generic filename — concurrent agents have silently replaced cached files at generic paths (p1.pdf, abs1.html, /tmp/tr.pdf) with a DIFFERENT paper mid-session while keeping the original mtime. Record each artifact's md5 after download and re-verify it immediately before AND after every extraction; if a hash changes, discard the derived analysis, re-download to a fresh path, and redo it. This is distinct from the network check below: repeat fetches compare responses, not the file on disk.
CRITICAL PDF CHECK: some PDFs carry a hidden, non-rendering text layer that does NOT match the visible document (pdftotext can pull the wrong layer). Confirm identity against what actually RENDERS: rasterize/inspect the cover page, cross-check the PDF metadata Title, and (for arXiv) the abs-page citation_title/citation_date meta tags.
CRITICAL FETCH CHECK: the HTTP path itself has been observed silently returning a DIFFERENT paper — a pdf whose metadata Title was right but whose text layer AND rasterized cover were another arXiv id, an /html/ URL that returned a third paper, and an abs page with a corrupted DOI. So fetch each surface (abs / html / pdf) AT LEAST TWICE and confirm the responses are consistent; if two fetches of the same URL disagree, keep re-fetching until they agree and say so in notes. Identity must be corroborated by at least TWO independent surfaces (e.g. abs-page citation_title AND the rasterized cover) — never a single one, in either direction. Then:
- Confirm the EXACT title, org/authors, and date. If wrong, put correct values in confirmed_* AND add a correction.
- Check every excerpt, key_fact, and factual claim in read_from_my_view/connections/worth_stealing against the source. Flag anything unsupported/overstated/misattributed — one correction {claim, issue, fix} each. Excerpts especially must be faithful to the report's own words/numbers; there should be 5-8 of them spanning method, training, numbers, eval setup, and a caveat — if the entry is thin or the excerpts miss the method or omit every caveat the report states, flag it so the reader can enrich it.
- 'connections' and 'worth_stealing' are interpretive links to the researcher's own notes/work; do NOT flag reasonable interpretation, ONLY claims that misstate what the source contains.
- FLAG AGENT/TOOLING PROCESS DETAIL AS A CORRECTION. If any field mentions scratch paths, file overwrites, concurrent agents, retry mechanics or directory collisions, file a correction telling the caller to DELETE that bullet: it is internal state, unusable by a reader, and it reads as doubt about the entry. Likewise, if the entry claims a URL served the wrong paper, try to reproduce it; if repeat fetches disagree with the claim, file a correction to drop or re-scope it to a non-reproducing transient rather than publishing it as a standing property of the URL.
- CHECK THE ENTRY'S 'uncertain' LIST BOTH WAYS. Items that are resolvable directly from the source (an affiliation printed on the rendered cover, a figure value present in the PDF text layer, a criterion the paper does state) should be filed as corrections that RESOLVE them — an entry that hedges what the source settles is unfinished, not merely cautious.
- leak_flags: list any phrasing that frames a model as the researcher's teacher/judge/base/internal training or eval dependency (e.g. "the teacher I lean on", "the model I use to grade/synthesize"), or names a private infra/method codename. These are confidentiality leaks and MUST be scrubbed before publishing even if factually true. Empty array if none.
- verdict: accurate | minor_issues | major_issues | could_not_fetch. If you cannot fetch, set could_not_fetch, explain in notes, do NOT fabricate confirmations.`;
}

phase('Read');
const results = await pipeline(
  SOURCES,
  (src) => agent(readPrompt(src), { label: `read:${src.id}`, phase: 'Read', schema: READ_SCHEMA, agentType: 'general-purpose' }),
  (summary, src) => {
    if (!summary) { log(`read failed: ${src.id}`); return null; }
    return agent(verifyPrompt(src, summary), { label: `verify:${src.id}`, phase: 'Verify', schema: VERIFY_SCHEMA, agentType: 'general-purpose' })
      .then((v) => ({ src_id: src.id, url: src.url, summary, verify: v }));
  }
);

const clean = results.filter(Boolean);
const flagged = clean.filter((r) => r.verify && r.verify.verdict !== 'accurate');
log(`done: ${clean.length}/${SOURCES.length} sources; ${flagged.length} need corrections applied before publishing`);
return clean;
