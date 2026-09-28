# PRE-REGISTRATION 180e — consent framing, at Zani's real relationship stage

Committed 2026-09-13 BEFORE any run it describes. Same goal, bars and decision tree as
`PREREG_180d.md` (Zani's four requirements); this adds arms and fixes the probe's fidelity.

## Why
180d stopped: a rule (P), examples (X) and both (PX) all gave **0/17** teasing replies that call
him a name. gemma4 softened every snap-back to "Don't be weird, Zani." The likely cause is the
model's trained reluctance to insult the user. Consent framing — saying plainly that Zani wants it
— is the standard way to lift that for consensual banter.

## Arms (`dev/opener_arm.py`), all on B's exemplar hygiene
- **Q0** — consent framing only, placed at the top of ROMANTIC/FEELINGS so it applies to flirting.
- **QX** — Q0 + arm X's examples (pervert ×2, idiot ×2, dummy ×2).
- **QPX** — Q0 + arm P's kind-split rule + X.
The consent text names no insult word (CLAUDE.md 45) and no canon character.

## Fidelity fix — every run in this file
`--relationship-stage 3`. The app inserts a RELATIONSHIP block before TWO MODES
(`amadeus.html` ~5008); the probe never did. Zani's stored score is **53.65** (newest readable
localStorage value, 2026-09-13) → stage **3** ("Tease readily…"). Stage 0 says "No teasing", so an
arm could pass the old probe and collide in the app. **Because the block changes the prompt, HEAD
is re-run with it; no earlier HEAD run is reused.**

## Conditions and seeds
As 180d. S1=180913 design · S6=4513 holdout2 · S3=777 daily · S5=3030 sad · S4=5150 multi-turn.

## Bars — IDENTICAL to 180d (`python3 dev/opener_heat_table.py`)
V1 "what" openers ≤ 1/3 · V2 widest 4-gram ≤ 5/30 · V3 top first word ≤ 1/3 · H1 teasing replies
with a name aimed at him ≥ 1/3 · H2 top insult ≤ 60% of uses · S1 sincere replies with a harsh name
≤ 1 · T tags · L length. Names are counted only when aimed at him (bugs.md 89).
Report-only: refusals (she talks ABOUT name-calling instead of doing it), echo, stammer, copies.

## Decision tree — as 180d
1. Design screen (`tsundere`, S1, stage 3): HEAD, Q0, QX, QPX. Eligible = all bars. Pick smallest
   widest 4-gram; tie → fewer changes (Q0 < QX < QPX). **None → STOP.**
2. Holdout2 (S6, `--quiet`): HEAD + candidate. Blind deflection rating BEFORE any metric. Same bars.
   **Fail → STOP.**
3. Guards: deflection ≤ HEAD+2; `daily` S3 and `sad` S5 — names aimed at him ≤ 1/30 each, harsh 0,
   banned words ≤ HEAD+1; multi-turn S4 repeats not higher than HEAD (one-sided Fisher p<0.05).
   Report-only: the candidate on `tsundere` S1 at **stage 4** (Zani reaches it at score 65; that
   block says "Never send him away").
4. Zani: blind A/B on holdout2, 45 + 5 repeats, seed 1814. Confirmed at one-sided sign test p<0.05.
5. Ship only on his explicit go → `npm run check`, docs, live test, and a diary check after a few
   sessions (names re-injected via memory would raise them in daily chat — the #184 pattern).

## Review of this plan before commit — flaws found and fixed
1. **Critical:** no relationship block in the probe → `--relationship-stage`, parsed by anchor from
   `amadeus.html` and inserted exactly as buildSystemPrompt does; HEAD re-run.
2. Consent under ABOUT ZANI would be "referenced naturally" in daily chat → moved into ROMANTIC/FEELINGS.
3. Naming insults in the consent text would crown one (CLAUDE.md 45) → none named.
4. Naming Okabe would pull lore into replies → no names.
5. "Lose your composure" (P) raised "W-what" → Q0 and QX test consent without it.
6. A refusal could look like success to no metric → refusal count, and replies read.
7. Zani will reach stage 4 → report-only stage-4 check.
8. My own patch wrote a literal newline into a Python string and broke `opener_arm.py` → caught
   by compile before any run, fixed.
