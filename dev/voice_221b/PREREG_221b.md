# PREREG_221b — her tsundere/flustered voice: which emotion, and do a newer model or the expressive voice help?

Written 2026-09-30, BEFORE any Stage 2a synthesis. Approved by Zani the same day: Stages 1 and 2a, on the
FREE model `s2.1-pro-free` (he accepted that Fish may keep free requests to improve its models).
CLAUDE.md 53: metrics only REJECT; his ear chooses; a live trial is the final gate. Scope: the VOICE only —
no change to her English text, the prompt, the translation, or the display. Nothing ships from this file:
Stage 2b (confirmation) and Stage 3 (paid check, ship) need a new plan and his yes.

Background (#221): short tags (H2) = no difference; re-anchoring (H1) = worse; speed (H3) closed by #225.
Research 2026-09-30: Fish auto-tags the shipped voice `c4d8…` "calm, measured, professional, neutral-tone";
the old voice `fb03…` "expressive, dynamic, energetic" (but also "middle-aged"). Fish: the reference carries
its emotional state; "different voices respond to the same tag with different intensity". `s2-pro` is now
"legacy"; Fish recommends `s2.1-pro` (same price; `s2.1-pro-free` is $0 until 2026-11-30).

## Stage 1 — which emotion sounds wrong? ($0, no synthesis)
- Clips: the 16 existing arm-A clips of `dev/voice_221/clips.json` (shipped config, s2-pro, `c4d8`), + 2
  repeats (seed 2210), random order. Each card shows the English line and the Japanese.
- Answer per clip: `right` / `too calm` / `too much`.
- Rule: an emotion NEEDS A FIX if `too calm` ≥ 4 of its 8 clips. Repeats are reported (agreement x/2).
- If NEITHER emotion needs a fix, Stage 2a is NOT shown; report and ask him (the cause may be the live
  context, not the audio).

## Stage 2a — pilot, blind A/B (arms)
All arms use the SHIPPED request, captured from the real `fs.fish_tts()` with `requests.post` mocked
(`arms_b.shipped_request`): same text (shipped tag + Japanese), same params. Only these change:
- **A**  = shipped: model `s2-pro`, voice `c4d8…`. A1 = the #221 `A` clip; A2 = the #221 `A'` clip, or a
  NEW paid draw where none exists.
- **M**  = model header `s2.1-pro-free`, voice `c4d8…`.
- **MV** = model header `s2.1-pro-free`, voice `fb03cde57e7740c38a9601459afaae42`.
M vs A = the model effect. MV vs A with M vs A = the voice effect on the new model.

**Lines (pilot set, by rule, no hand-picking):** the odd-numbered frozen lines of `dev/voice_221/lines.json`:
t1 t3 t5 t7 f1 f3 f5 f7 (4 fish.log + 4 E1; 4 tsundere + 4 flustered). The even lines are kept UNHEARD in
any new arm for a later confirmation (2b), so a pilot winner is not confirmed on the lines that chose it.
**Draws:** 2 per arm per line (M1 M2 MV1 MV2 on every pilot line; A2 new for t3 t5 t7 f3 f5 f7).

**Sheet (`blind_b.py`, seed 2211):** per line A1 vs M1, A2 vs M2, A1 vs MV1, A2 vs MV2 = 32 test items;
+ 4 of them repeated with sides flipped; + 4 noise items A1 vs A2 (t1 t5 f1 f5) = 40, random order and sides.
Question: "Which one do you want her to sound like here?" A / B / =. Per clip: `broken` (English, glitch,
dead air) and `not her` (does not sound like Kurisu). A broken or not-her CANDIDATE clip = a loss for that
pair. **Level-matched:** every sheet copy gets a gain so its integrated loudness equals the median of the A
clips (standard listening-test practice; louder is heard as better). The native loudness gap is reported.

## Screens (reject only; app CLOSED — Whisper uses the GPU)
- **Loop:** a clip longer than 2x the median A duration of its line = broken (auto loss in its pairs).
  An arm with ≥ 2 loop clips FAILS.
- **English bleed / pauses:** the PREREG_221 rules, with A = all A1+A2 pilot clips as the calibration.
  An arm FAILS if its flags exceed A's + 2 (of 16).
- **Reported, not a gate:** median LUFS gap vs A (native), median pitch shift in semitones vs A (voice
  identity), median duration ratio vs A.

## Decision (pilot)
Consistency on flipped repeats must be ≥ 3/4, or the sheet is untrusted (report, no decision).
An arm ADVANCES to a 2b plan only if ALL hold:
1. pair wins ≥ pair losses + 4 (of its 16 pairs);
2. lines with net > 0 ≥ lines with net < 0 + 2 (net = its wins − losses over the line's 2 pairs);
3. `not her` on ≤ 2 of its 16 clips;
4. every screen passes.
Both advance → the higher pair net; equal → M (the smaller change). Neither → stop; next options are
temperature for tsundere/flustered only, or the Japanese wording (H4). Per emotion: wins/losses are reported
next to the Stage 1 result (an arm that wins only where Stage 1 found no problem is noted).

## Cost cap
Guard (`common.Guard`, bytes × $15/1M × 1.5) counts EVERY call as if paid, so a free model that bills by
mistake is still bounded: cap **$0.30**. Expected real spend: only the 6 new A2 clips on s2-pro (~$0.03).
Wallet read before and after; it lags, so it is read again at the next session.

## OUTCOME (2026-10-04)
M advanced from 2a; confirmed and shipped through `dev/voice_221b2/PREREG_221b2.md` (with a loudness fix). Zani kept it.
