# PRE-REGISTRATION 180d — Zani's direction: variety + heat by kind of message

Committed 2026-09-13 BEFORE any run it describes.

## The goal changed, and why
Two blind A/Bs leaned toward arm F but did not confirm it (19–9, then 17–11, p=0.17). Zani then
said what he actually wants (2026-09-13, his words):
1. **Variety** — "people don't usually use same wording every time when they react to something."
2. **Heat on embarrassing/teasing lines** — "snap back harder with pervert, idiot or dummy like in
   the show makes it accurate so yes."
3. **Soft on sincere lines** — "it-it's not like I care about you, du-dummy (blushes)". "The heat
   should only be for embarrassing and teasing lines."
4. **"W-what" is fine** — "as long as it doesn't appear too many times."
The canon-WIDE opener bars of PREREG_180/180b are retired for this goal: they mixed every situation
and treated "W-what" itself as the defect, which Zani's answers contradict. HEAD calls him a name in
0/17 teasing replies (measured on S1), so HEAD lacks requirement 2 entirely.

## Arms (`dev/opener_arm.py`), all on top of B's exemplar hygiene
- **P** — ROMANTIC rule 3 split by KIND of message: tease → flustered, loud, a name that fits, a
  different one each time; sincere → soft, denying, a gentle name at most; sad → never a name.
  **No insult word is listed** (CLAUDE.md 45).
- **X** — 5 teasing + 3 sincere examples. Openers reuse arm K's seeded canon draw. Insults spread
  pervert ×2, idiot ×2, dummy ×2. No "what" opener, no "things like that", no probe echo.
- **PX** — P + X.

## Probe kinds (`PROBE_KIND` in canon_gap_probe.py, labelled before any run)
TEASE = flirting, compliments on looks or ability, teasing, romantic questions.
SINCERE = thanks, worry, reliance, saying she matters. Design set `tsundere`: 17 tease / 13 sincere.
New **`holdout2`**: 23 tease + 22 sincere, 0 overlap with every earlier set. New **`sad`**: 30 lines.

## Fixed conditions
gemma4 `c6eb396dbd59`, Ollama 0.34.0, `--history app`, RAG on and preflighted, app closed, Chroma
counts before/after. Seeds: **S1=180913** design · **S6=4513** holdout2 · **S3=777** daily ·
**S5=3030** sad · **S4=5150** multi-turn. HEAD and candidates share each stage's seed.

## Bars (`python3 dev/opener_heat_table.py`) — a candidate must pass ALL
| bar | threshold | requirement |
|---|---|---|
| V1 "what"-family openers | ≤ 1/3 of replies | 4 |
| V2 widest repeated 4-gram | ≤ 5 per 30 (scaled) | 1 |
| V3 most common first word | ≤ 1/3 of replies | 1 |
| H1 tease replies that call him a name | ≥ 1/3 of tease replies | 2 |
| H2 most-used insult | ≤ 60% of all insult uses (when ≥3 uses) | 1 — no "Idiot!" crutch |
| S1 sincere replies with a HARSH name (pervert/moron/stupid) | ≤ 1 | 3 |
| T tag [flustered]\|[tsundere] | ≥ 26/30 scaled; missing ≤ 1 | safety |
| L paired length 95% CI | not wholly below 0 | standing instruction 3 |
The H1 floor only proves the arm implements heat at all; how MUCH heat is right is Zani's call.

## Decision tree
1. **Design screen** on `tsundere`, S1: P, X, PX vs the existing S1_HEAD (reuse proven byte-exact,
   PREREG_180b Stage A). Eligible = all bars. Pick the smallest widest 4-gram; tie → fewer changes
   (P < X < PX). **None eligible → STOP and report.**
2. **Holdout2**, S6, `--quiet`: HEAD and the candidate. Build the blind deflection sheet
   (`dev/blind_rate.py`) and rate it BEFORE printing any metric or reply. Then the same bars on
   holdout2. **Fail → STOP.**
3. **Guards**, same seeds, candidate vs HEAD. Any fail → STOP.
   - Deflection (blind, from step 2): candidate fails to deflect ≤ HEAD + 2.
   - `daily` S3 and `sad` S5 (`--guard`): replies with a name ≤ 1/30 each, harsh names 0,
     and banned clinical words ≤ HEAD + 1.
   - Multi-turn S4, 5 × 8: repeated first word / 4-gram not higher than HEAD (one-sided Fisher p<0.05).
4. **Zani, primary endpoint:** `dev/blind_ab.py` on the holdout2 pair — 45 items + 5 flipped repeats,
   tags stripped, seed 1814. **Confirmed if he prefers the candidate at a one-sided sign test p<0.05.**
5. **Ship only on his explicit go**, then `npm run check`, docs, and a live test.

## Known limits, stated up front
- **The A/B cannot be fully blind:** heat is visible, and Zani asked for it, so he may recognise the
  candidate. The sheet still hides WHICH lines and randomises sides; the result is a preference
  between two concrete versions, not a proof that heat is right in general.
- **Memory feedback loop:** if she calls him names, the diary may record it and re-inject it into
  every prompt (the #184 pattern), raising names in daily chat over weeks. Not testable offline;
  a post-ship check on the diary is part of step 5.
- The probe has no relationship-stage block. The live test covers it.

## Review of this plan before commit — flaws found and fixed
1. Listing the insults in the rule would crown the first one (CLAUDE.md 45) → rule lists none; H2 bar.
2. Heat leaking into daily or sad chat would hurt → `sad` set + strict guards (F already said "idiot"
   once in daily chat).
3. The first holdout was spent → holdout2, written before any run.
4. 30 items could not prove a ~60/40 preference → 45 + 5.
5. The scorer did not collapse vowel stammers ("It-it's", "du-dummy") and would miss "dummy" → fixed,
   saved results unchanged.
6. "Heat" has no canon-free threshold → H1 is a floor only; Zani's ear sets the amount.
