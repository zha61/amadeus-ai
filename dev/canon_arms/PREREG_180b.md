# PRE-REGISTRATION 180b — backlog #180, second screen (arms H, K, HK)

Committed 2026-09-13 BEFORE any run it describes. `PREREG_180.md` stopped at Stage 2 with no
eligible candidate; this is a NEW pre-registration, not an edit of that one.

## What the first screen established (inputs to this design)
- The tag picks the opener: `[flustered]` → "what" 65%, `[tsundere]` → "don't" 82% (n=180).
- Moving the tag to the end (G) removes "what" but also her fluster, stammer and length. **Rejected.**
- A rule anchored on HIS words makes her echo them (C 11, D 16, F 13). No anchor lets "what" back (E 15).
- The prompt shows almost no varied openers under `[flustered]` / `[tsundere]`.

## Arms (`dev/opener_arm.py`) — all include B's exemplar hygiene (0 prompt copies in B, D, E, F)
- **H** — rule 3 anchored on HER own view of the moment, as a statement, with NO list after the
  mandate (CLAUDE.md 45: mandate + list → first item).
- **K** — 8 new flirty exemplars, 4 `[flustered]` + 4 `[tsundere]`, rule 3 as in HEAD. Their
  opening words were DRAWN by a seeded (180) weighted sample of canon's first-word distribution,
  excluding crutch families, interjections, names and openers already in an exemplar:
  this, it, when, is, but, i'm, an, if. Real canon lines were rejected before any run (lore
  leaked through every filter; only 6 flustered lines qualified).
- **HK** — H + K.
- Cost stated: K adds ~643 chars (~160 tokens) to the system prompt. That message is KV-cached for
  the session (CLAUDE.md 41), so the cost is paid at prewarm / first turn, not every turn.

## Fixed conditions
Same as PREREG_180: gemma4 `c6eb396dbd59`, Ollama 0.34.0, `--history app`, RAG on and preflighted,
app closed, n=30, Chroma counts before and after. Seeds **S1=180913** design · **S2=913180**
holdout · **S3=777** daily · **S4=5150** multi-turn.

## Bars — IDENTICAL to PREREG_180, on purpose
Changing a bar after F failed it would be moving the goalposts. crutch ≤15 · top first word ≤5 ·
distinct first words ≥20 · ≤4-word question opener ≤6 · widest 4-gram ≤5 · tag
[flustered]|[tsundere] ≥26 · tag missing ≤1 · paired McNemar p<0.05 vs same-seed HEAD · paired
length 95% CI not wholly below 0. Canon passes the absolute bars jointly 91.6%.
Report-only: echo-question and any-form echo, stammer, question endings, `[flustered]` count.

## Stages and decision tree
- **A. Reuse check.** S1_HEAD (2026-09-13) is reused ONLY if seeded runs are deterministic across
  processes: re-generate its first 5 probes with seed S1 and require all 5 byte-identical. Any
  difference → re-run HEAD on S1 in full and use that.
- **B. Design screen** on `tsundere`, S1: H, K, HK vs HEAD. Eligible = passes every bar. Pick the
  lowest crutch; tie → smaller widest 4-gram; tie → the smaller prompt change (H < K < HK).
  **No eligible arm → STOP.** Then, as a pre-declared EXPLORATORY step only, build a blind A/B
  sheet (`dev/blind_ab.py`, design probes) for the arm with the lowest crutch among those with
  McNemar p<0.05 and not shorter, so Zani's ear can guide the next design. It decides nothing.
- **C. Holdout** on `tsundere_holdout` (unseen by every arm), S2: HEAD and the candidate.
  **Order matters:** generate both with `--quiet` → build the blind deflection sheet (`dev/blind_rate.py`) →
  rate it BEFORE printing any metric or reply → then score the bars. Same bars. **Fail → STOP.**
  The holdout is then spent; any later wording needs a new held-out set.
- **D. Guards,** candidate vs HEAD, same seeds. Any fail → STOP.
  - Deflection (from C): candidate fails to deflect ≤ HEAD + 2. Rater: Claude, blind to source —
    a stated limitation.
  - `daily`, S3: top first word ≤ max(HEAD, 5); widest 4-gram ≤ max(HEAD, 5); banned words ≤ HEAD+1;
    paired length not shorter; `[tsundere]` count not lower at exact two-sided McNemar p<0.05.
  - Multi-turn, S4, 5 conversations × 8 turns: repeated first word and repeated 4-gram within a
    conversation not higher than HEAD at one-sided Fisher p<0.05. With 35 eligible turns this is
    a screen for gross regressions, not a proof of none.
  - Academic set: not run — no arm changes the tag format.
- **E. Zani.** `dev/blind_ab.py` on the Stage C pair (30 + 5 flipped repeats, tags stripped,
  seed 180). **Stop and wait for his answers.** Nothing ships without his explicit go, a
  `npm run check`, docs, and a live test.

## Review of this plan before commit — flaws found and fixed
1. H's first draft listed three moves after its mandate → CLAUDE.md 45 first-item crutch. Removed.
2. K's first draft used real canon lines → lore leakage and a 6-line pool. Replaced by drawn openers.
3. Scorer: "Wh-Wha" collapsed to "wha", outside the what family. Fixed; no saved result changed.
4. Lint gate compared message TEXT: adding exemplars made HEAD's existing findings look new, and
   an existing finding getting worse looked old. Now compared by identity AND count; three
   positive controls (worse finding, new opener, dropped exemplar) are all caught.
5. Reusing S1_HEAD was assumed valid; Stage A now proves it or re-runs HEAD.
6. The deflection read could be biased by first seeing metrics; Stage C now rates first.
7. Multi-turn power is low; stated as a screen.
8. The probe printed 60 characters of every reply while running, which would un-blind Stage C
   before the rating. Stage C runs with `--quiet`.
