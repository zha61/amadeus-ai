# PREREG_221 — her tsundere/flustered VOICE sounds too calm (backlog #221)

Written 2026-10-01, BEFORE line selection and BEFORE any arm synthesis. Approved plan: the
revised plan of 2026-09-30/10-01 (32 flaws fixed). CLAUDE.md 53: metrics can only REJECT an arm;
Zani's ear on the blind sheet chooses what goes to a live trial; the live trial is the final gate.
Scope: the VOICE only. No change to her English text, the system prompt, or the display layer.

## Step 0 — already run (result fixed here)
Same text, shipped `fish_tts()`, top-level `speed` 0.6 vs 1.8: 7.73s vs 8.05s, ratio 0.96 →
**IGNORED**. Positive control, `prosody.speed` 0.6 vs 1.8: 13.06s vs 4.21s, ratio 3.11 → the effect is
detectable. So `"speed": 1.1` (kurisu_fish_server.py) has no effect; she speaks at Fish's default 1.0.
**Step 0 changes no arm and no code.** Speed is Zani's decision (H3); every arm keeps the shipped payload.
Estimated cost $0.026 (4 clips). The wallet did not move — Fish bills with a delay — so the cost guard
counts bytes x $15/1M x 1.5 instead (`common.Guard`).

## Arms (text only; the payload is the shipped `fish_tts()` for all)
Defined ONLY in `arms.py`. A = shipped. B = short rule-32 tags. C = B + re-anchor at each later sentence
start. D = A tag + C anchors (conditional). Only `tsundere` and `flustered` change.

## Line selection rule (applied by `select_lines.py`, no hand-picking)
- **fish.log** (`data/logs/fish.log`, the "Full tagged text" lines, file order): emotion from the
  preceding `Received … emotion=` line; Japanese = text after the leading `[…]` tag.
- **E1** (`dev/canon_arms/E1_HEAD.txt.json`, probe order; SYSTEM_PROMPT byte-identical to HEAD, 10,061
  chars): only `probe` and `reply` are read, never `rag_block`. Tag from the reply's `[EMOTION:x]`.
  Japanese = shipped `translate_via_gemma()` (imported), ONE call, frozen, never re-translated.
  App must be closed (pgrep) — gemma4 (CLAUDE.md 37).
- Keep a line only if its **Japanese** has ≥2 sentences (`arms.sentences`).
- Duplicate key: the English reply (fish.log: the Japanese) without its first word, lowercase, letters
  only. A duplicate is skipped.
- **Tsundere (8):** first 4 fish.log tsundere + first 4 E1 tsundere.
- **Flustered (8):** every fish.log flustered (1) + first 7 E1 flustered.
- A' (second synthesis of arm A, noise control): tsundere items 1–2 and flustered items 1–2.

## Screens (reject only)
- **Pauses** (`common.internal_pauses`, -35dB / 0.15s, silence touching start or end dropped). A clip is
  FLAGGED if any internal pause > 1.2s, or its count of internal pauses > 0.6s exceeds its number of
  sentence boundaries. An arm FAILS if its flagged clips > (A's flagged clips + 2), of 16.
- **English bleed** (local mlx-whisper large-v3-turbo, language='ja'): a clip is FLAGGED on a run of ≥3
  Latin letters, or ≥4 unmatched characters before the first character matched to the source Japanese.
  Calibrated on arm A first (live A had no English, Zani 2026-09-30): if A has > 2/16 flags, the screen
  is untrusted and only marks clips for his ear. Otherwise an arm FAILS if flags > A's flags + 2.
- **Loudness** (ffmpeg ebur128, integrated LUFS, NOT normalised): reported. If an arm's median is > 2 LU
  above A's, it is reported as a possible confound.

## Blind sheet (`blind_audio.py`, seed 221)
Per line: A vs B and A vs C (32) + 5 of them repeated with sides flipped + 4 A vs A' = 41 items, random
order, random sides, opaque file names, no arm label in the page. Question: "Which one do you want her
to sound like here?" Answers A / B / = ; a separate "broken" box per clip (English, glitch, dead air).
A broken candidate clip counts as a LOSS for that pair. A broken A clip is recorded; the pair answer stands.

## Decision rule
An arm goes to a live trial only if ALL hold: exact one-sided sign test on its non-tie pairs vs A,
p ≤ 0.10; wins ≥ 8; consistency on the flipped repeats ≥ 4/5; both screens pass.
- Both B and C pass → more wins; equal → B (fewer tags).
- Per emotion: if an emotion has losses > wins for the chosen arm, ship it for the other emotion only.
- B fails its test but C passes → run D (16 clips) and a short second sheet (D vs A, same rules) first.
- A vs A' is reported (his non-tie rate on same-config pairs = Fish's own variation); the sign test
  already assumes 50/50 under no difference, so it stays valid.
- Nothing passes → stop and report. Next hypotheses need a new plan and his yes: H4 (the Japanese
  wording, touches #196), H6 (neutral reference voice `c4d8…` vs the old expressive `fb03…`).
  Recorded, unproven: H5 — the shipped tags (189 / 167 chars) plus Japanese always exceed
  `chunk_length` 200. A B-win cannot separate wording from length.

## Ship (only on Zani's yes)
Tag `pre-221`; one commit byte-identical to the chosen arm (test: shipped `/speak`, mocked translate and
Fish, all 16 lines == `arms.tagged_text`; mutants: anchor missing on sentence 2, anchor on another
emotion, anchor after the last sentence, 1-char tag change; rule-32 fragment check). `very_blush` =
`flustered`. `GREETING_TTS_VER` v3 → v4 whenever EMOTION_TAGS change, and for D. Revert:
`git checkout pre-221 -- kurisu_fish_server.py amadeus.html`, relaunch.

## Cost cap
$0.40 total (Zani, 2026-10-01), estimated by `common.Guard`, including Step 0.

## Erratum (added after scoring)
The date "2026-10-01" above is wrong: every step ran on **2026-09-30**. Nothing else changed.
