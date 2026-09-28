# PRE-REGISTRATION — backlog #180, her opener crutches, stages 1–5

Written and committed 2026-09-13 BEFORE any run it describes. Nothing below changes after a
result is seen. If a rule here turns out wrong, the run is reported as it stands and the
change is a NEW, separately committed pre-registration.

## Fixed conditions (every run)
- `dev/canon_gap_probe.py`, gemma4:latest `c6eb396dbd59`, Ollama 0.34.0 (recorded per row)
- `--history app`: a greeting from the real `GREETINGS` array in the app's `[EMOTION:x] text` form
- RAG on, server verified by preflight; app closed (the probe refuses otherwise)
- n=30 per single-turn run; Chroma row counts recorded before the first run and after the last
- Seeds: **S1=180913** design (stages 1–2) · **S2=913180** holdout (stage 3) ·
  **S3=777** daily + academic guards · **S4=5150** multi-turn. HEAD and every arm in a stage
  share that stage's seed, so comparisons are paired by probe AND seed.

## Arms (`dev/opener_arm.py`)
- **HEAD** — unchanged prompt.
- **G** — HEAD + emotion tag at the END (instruction, 38 exemplars, history). Diagnostic.
- **F** — B's exemplar edits + a rule 3 that makes the opening HER statement about his detail.
- **FG** — F + G.
- D and E are closed: D fails by eye (echo-question 18/30), E fails its bar (22/30).

## Hypotheses
- **H1 (mechanism):** G lowers the "what"-family opener vs HEAD. Exact one-sided McNemar p<0.05.
  Not a gate — it decides only whether the tag explanation is supported.
- **H2 (fix):** a candidate lowers the crutch family vs HEAD AND meets every bar below.

## Primary endpoint
Crutch family = first word, stammer collapsed, in {what, what's, don't}. Scored by
`dev/opener_family.py`, paired exact one-sided McNemar vs the same-stage HEAD run, **p<0.05**.

## Bars (a candidate must meet ALL)
| measure | bar | basis |
|---|---|---|
| crutch family | ≤15/30 | approved target 2026-09-12 |
| most common first word | ≤5/30 | canon n=30 p95 |
| distinct first words | ≥20/30 | canon n=30 p5 = 21 |
| ≤4-word question opener | ≤6/30 | canon n=30 p95 |
| most widespread 4-gram | ≤5/30 | HEAD 12; canon p95 2 — an intermediate step, stated as such |
| tag [flustered]\|[tsundere] | ≥26/30 | ROMANTIC rule 1 |
| tag missing | ≤1/30 | parsEmo → 'default' |
| paired length ARM−HEAD | 95% CI not wholly below 0 | standing instruction 3 |

**Known limits, stated up front:** canon itself passes the absolute bars jointly only 91.6%
of the time (1000 resamples), so a truly canon-like candidate fails by chance ~8%. Canon mixes
every situation, while these probes are all flirty, so canon-derived ceilings are strict, not lax.

## Decision tree
1. **Stage 1:** HEAD(S1) and G(S1) on `tsundere`. Report H1.
2. **Stage 2:** F(S1) and FG(S1) on `tsundere`. Eligible candidates = G, F, FG that pass the
   primary endpoint and every bar. Choose the lowest crutch count; tie → the smaller widest
   4-gram; tie → the arm WITHOUT G (smaller ship change).
   **No eligible candidate → STOP and report. No new wording without Zani's approval.**
3. **Stage 3:** HEAD(S2) and the candidate(S2) on `tsundere_holdout` (never seen by any arm).
   Same endpoint, same bars. **Fail → STOP and report.**
4. **Stage 4 guards,** candidate vs HEAD on the same seeds. Any fail → STOP and report.
   - `daily` (S3): most common first word, widest 4-gram and banned words not above
     max(HEAD, bar); length not shorter; `[tsundere]` share not lower at exact two-sided
     McNemar p<0.05 (small talk → [tsundere] by default).
   - `academic` (S3), **only if the candidate contains G:** tag missing ≤1/30; truncations not
     above HEAD+1; `[lecture]|[curious]` share not lower at McNemar p<0.05.
   - multi-turn (S4), 5 conversations × 8 turns, alternating daily / held-out flirty:
     within-conversation repeated first word and repeated 4-gram not higher than HEAD at
     one-sided Fisher p<0.05. (Histories diverge, so turns cannot be paired.)
   - deflection, read blind: HEAD and candidate holdout replies mixed, tags stripped, labels
     hidden. A reply FAILS to deflect if it accepts the compliment or feeling plainly or
     answers the flirty question directly. Fail if the candidate has ≥3 more failures than
     HEAD. Rater: Claude — a stated limitation, which is why Stage 5 exists.
5. **Stage 5:** `dev/blind_ab.py` on the Stage 3 pair — 30 items + 5 flipped repeats, tags
   stripped, sides randomised (seed 180). Zani answers A / B / =. Reported: preferences,
   exact sign test, consistency on the repeats. **Not a gate: Zani decides.**
6. **Ship** only on Zani's explicit go. If G is in the candidate, first audit every tag
   consumer: 10 `history.push` sites, the directives at `amadeus.html:2262` and `:2979`,
   greetings, diary, and truncation. Then `npm run check` and a live test.

## Multiple comparisons
Three candidates are screened on the design set. That selection is why Stage 3 exists: the
confirmation uses unseen probes, fresh seeds, and one pre-chosen candidate.
