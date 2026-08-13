---
name: paper-main-appendix
description: Structure a paper so the main body lands ONE core message within the venue page limit and all supporting detail moves to a technical appendix. Use when a draft is over length or buries its thesis in detail/hedges.
---

# One-message-first, appendix-for-the-rest

A paper must deliver ONE core message that a reader gets from the main body alone. Content that
only *supports* understanding goes to a technical appendix (a separate supplementary PDF at most
venues; reviewers are not obliged to read it).

## Procedure
1. **Verify the venue page limit first** (web-search it; don't assume). E.g. AAAI-26 = 7 pages
   technical content; references + reproducibility checklist do NOT count; technical appendix is a
   separate supplementary PDF.
2. **Write the core message as one sentence.** Everything in the main body must visibly serve it.
3. **Allocate:**
   - MAIN: intro + motivation figure; brief method (enough to trust); THE headline result with its
     one table/figure; the payoff experiments that justify the contribution; short discussion +
     load-bearing limitations + conclusion.
   - APPENDIX: ablation mechanics, robustness checks, per-X breakdown tables, reproducibility
     deep-dives, secondary audits, extended limitations, dataset/datasheet mechanics, extra figures.
4. **Cut the verbose trap:** one claim per sentence; remove connective filler ("The finding is
   sobering", "Tellingly", "Finally"); state each hedge ONCE where the claim is made and point to
   the appendix for the full accounting (do not restate a caveat 3x). Headline number in main;
   CIs / per-model splits / n's in the appendix.
5. **Keep honesty non-negotiable** — a retraction or limitation stays, but stated crisply once.
6. **Verify after each move:** rebuild; 0 undefined refs; main body <= the page limit (count to the
   start of references).

## Mechanics
Keep main sections separate from appendix sections; include appendix after the conclusion via
`\appendix` for the working build, and split it into the supplementary PDF at submission.
