# PRE-REGISTRATION 180f — example CONVERSATIONS before the history

Committed 2026-09-19 BEFORE any run it describes. Goal, bars and decision tree are those of
`PREREG_180d.md` (Zani's four requirements), at his real relationship stage as in `PREREG_180e.md`.

## Why
Rule (P), listed examples (X), both (PX) and consent framing (Q0/QX/QPX) gave 0–3 of 17 teasing
replies that call him a name (bar ≥ 6). Models imitate earlier conversation TURNS much more
strongly than listed examples (CLAUDE.md 47 is the same effect). This is the last strong
prompt-level mechanism; Zani chose it ("option1 first will do").

## Arms (`dev/opener_arm.py`, `EXAMPLE_TURNS`)
- **T** — B's exemplar hygiene + 9 example exchanges placed between the system prompt and the real
  history: 5 teasing (names), 2 sincere (one soft "dummy"), 1 sad and 1 daily (no names). Names
  spread pervert ×2, idiot ×2, dummy ×2; 9 different first words; no "what" opener. Framed by a
  system line saying they are examples that did not happen, and a closing line.
- **TQ** — T's turns + the Q0 consent statement.

## Conditions
gemma4 `c6eb396dbd59`, Ollama 0.34.0 (both re-checked 2026-09-19), `--history app`, RAG on and
preflighted, app closed, `--relationship-stage 3` (score still 53.65; the app was not used since
2026-09-13; diary still 60 rows). Seeds as 180d/180e: S1=180913 · S6=4513 · S3=777 · S5=3030 · S4=5150.

## HEAD reuse
`E1_HEAD` (180e, stage 3, S1) is reused ONLY if its first 5 probes regenerate byte-identical today.
Otherwise HEAD is re-run in full.

## Bars — identical to 180d/180e, plus two report-only measures
Report-only: **leak** (a reply mentions an example-only topic: mirror, handwriting, coffee, lab coat,
homework, reread, comebacks) and copies of example lines (the copy check now includes the turns).

## Decision tree — as 180d
Design screen (S1) → holdout2 (S6, quiet, blind deflection rated first) → guards (daily S3, sad S5,
multi-turn S4, deflection) → Zani's blind A/B (holdout2, 45 + 5, seed 1814, one-sided p<0.05).
Any stage fails → STOP. Nothing ships without his explicit go.

## Ship-time requirements, stated now so they cannot be forgotten
1. The turns are injected only when a request is BUILT. They must NEVER be pushed into `history`:
   the diary (`amadeus.html:3969`) and the fact extractor (`:4192`) read `history`, so fake
   exchanges there would become her memory.
2. All four request builders (`amadeus.html:2263`, `:2582`, `:2980`, `:3251`) and the prewarm (~`:5099`)
   must share ONE helper, or the KV prefix diverges and the first turn re-prefills (rule 33 family).
3. Cost: ~337 tokens, static, inside the cached prefix — paid at prewarm, not per turn.
4. `npm run check`, docs, a live test, and a diary check after a few sessions.

## Review of this plan before commit — flaws found and fixed
1. Examples could be taken as real events → framed as examples; report-only leak check.
2. The lint gate and the copy check could not see example turns → both now include them
   (`lint_lines`), and the lint delta is 0.
3. Teasing-only examples would teach "always snap" → sincere, sad and daily contrast turns.
4. Two examples shared a topic with held-out probes ("smug", "date") and could be copied onto them,
   inflating heat → replaced; no distinctive word now overlaps any flirty probe set.
5. A misplaced example block would test the wrong thing → GPU-free mock verified the exact message
   order in single-turn and multi-turn mode, and that no example text enters the history.
6. Six days passed → model digest, Ollama version, diary size and relationship score re-checked.
