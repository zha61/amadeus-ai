# PREREG_221b2 — confirm s2.1-pro (same voice `c4d8`) for her tsundere/flustered voice, at s2-pro's loudness

Written 2026-10-01, BEFORE any Step 0 / 2b / Stage 3 Fish call. Zani approved Stage 2b on 2026-10-01 and
then asked: "check plan again … fix all flaws … Then proceed." The cost still needs his separate yes. CLAUDE.md 53: metrics only REJECT; his
ear chooses; a live trial is the final gate. Scope: the VOICE only — no change to her English text, the
prompt, the translation or the display (CLAUDE.md 51). Free model `s2.1-pro-free` is approved for TEST
clips only (he accepted its data-use terms). Only the PAID `s2.1-pro` may ship.

Background: Stage 1 — 18/18 current clips "too calm" (both emotions). Stage 2a — M (`s2.1-pro-free`, `c4d8`)
beat A 15-1 (p=0.00026), 0 "not her"; it advances (`voice_221b/result_2a.json`). s2.1 is ~8.5 LU louder
(A median −22.0 LUFS, M −13.45; per clip +7.2…+10.8). Fish documents `prosody.volume` (dB, 0 = none) and
`prosody.normalize_loudness` (default true on S2); it does not say which applies first.
**Why loudness is a gate:** lip sync (`AMPLITUDE_GAIN=3`, `SILENCE_THRESHOLD=0.012`) and BGM ducking were
tuned at s2-pro's level; +8.5 LU ≈ 2.7x amplitude would pin her mouth open.

## Arms (`arms_b2.py`, the only definition; built from the real `fish_tts()` request, mocked post)
- **A** — shipped: `s2-pro`, `c4d8`, no `prosody`.
- **M** — `s2.1-pro-free`, no `prosody` (Step 0 baseline only).
- **C** — `s2.1-pro-free` + `"prosody": {"volume": V}` — **the candidate; byte-identical to the ship
  request except the model header.** V is fixed by Step 0.
- **P** — `s2.1-pro` + the same `prosody` (Stage 3; exactly the ship request).
`normalize_loudness` is NOT sent (Fish default). No `speed` anywhere (#225).

## Lines (`lines_b2.json`, frozen by `freeze_lines.py` before any call)
- **Target (8):** t2 t4 t6 t8 f2 f4 f6 f8 of `voice_221/lines.json` — no NEW arm has used them.
  (Zani heard their A clips in Stage 1; accepted and stated.)
- **Guard (8):** `data/logs/fish.log`, "Full tagged text" lines in file order, tag must equal the shipped
  tag, Japanese ≥ 2 sentences; the first 2 of each of teasing, sarcastic, dismissive, curious.
  Frozen with the log's sha256 (the log grows and rotates). Log lines 16/253, 37/184, 55/112, 193/271.
  Only 4 of 20 emotions are guarded; the live trial covers the rest (stated limit).

## Step 0 — loudness (`step0.py`; free model only)
t2 and f2; 3 draws each of M and C at **V0 = −8.5 dB**, interleaved (12 clips). Target = **−22.0 LUFS**
(median of the 16 s2-pro A clips, `voice_221b/screens_b.json`). PASS if ALL:
1. volume acts: median(M) − median(C) ≥ 5 LU;
2. level: |median(C) − (−22.0)| ≤ 1.0 LU;
3. peak: max true peak of C ≤ −1.0 dBTP;
4. duration: median over the 2 lines of (median C dur / median M dur) in [0.92, 1.08];
5. pitch: median over the 2 lines of the C-vs-M shift within ±1.0 semitone (rough estimator, relative).
**One correction only**, and only if 1, 3, 4, 5 pass and 2 fails: V1 = V0 − level error, rounded to 0.5 dB;
6 more C clips at V1; re-decide with V1. Anything else failing → STOP and ask Zani (default answer to plan
question 3: stop and ask; a server-side gain step is NOT tried without his yes).
`step0_result.json` is committed BEFORE any 2b call; `synth_b2.py` refuses to run unless it says passed.

## Stage 2b — confirmation (`synth_b2.py`, `screens_b2.py`, `blind_b2.py`)
Draws: A1, A2 (s2-pro, the real shipped `fish_tts`) and C1, C2 on all 16 lines. Reused, never re-made: #221
A as A1 for the 8 target lines; #221 A′ as A2 for t2, f2 (text asserted equal to the shipped text; made
with the ignored top-level speed field, so the audio config is the same — #225). New: 22 paid A clips,
32 free C clips. The first call is a free smoke call.
**Screens (reject only; app CLOSED — Whisper):** PREREG_221b rules. C FAILS on: ≥ 2 loop clips (> 2x the
line's median A duration); bleed flags > A's + 4 (of 32); pause flags > A's + 4; **native median LUFS gap
C − A beyond ±1.5 LU** (the Step 0 fix must hold on all 16 lines). True peaks > −1 dBTP are reported.
**Sheet (seed 2212):** per line C1 vs A1, C2 vs A2 = 32 test pairs + 4 flipped repeats + 4 A1-vs-A2 noise =
40 items, random order and sides, level-matched to the A median, no arm label. "Which one do you want her to
sound like here?" A / B / =. Per clip: `broken`, `not her`, `too much`. A break note at item 21. Same
headphones as in the app. A broken / not-her / looping C clip = a LOSS for its pair.
**C PASSES only if ALL:**
1. consistency on the flipped repeats ≥ 3/4 (else untrusted: report, no decision);
2. exact one-sided sign test on the 16 TARGET pairs (ties dropped) p ≤ 0.05 (e.g. 12-4 passes, 10-6 fails);
3. target lines with net > 0 ≥ lines with net < 0 + 2;
4. tsundere wins ≥ losses, and flustered wins ≥ losses (target pairs);
5. `not her` on ≤ 2 of the 16 target C clips;
6. GUARD: guard losses ≤ guard wins + 2 (of 16), and `not her` on ≤ 2 of the 16 guard C clips;
7. every screen passes.
`too much` counts and the A1-vs-A2 non-tie rate are reported, never gates. Two pairs on one line are not
independent — rule 3 is the per-line check. Fail → stop; nothing ships; report to Zani.

## Stage 3 — the paid model equals the free one (`synth_b2.py --stage3`; only after 2b passes)
P on t2 t6 f4 f8 + g_teasing1 g_sarcastic1 g_dismissive1 g_curious1 (8 clips). Screens vs the same lines'
C clips — PASS if ALL: median |LUFS(P) − median LUFS(C of the line)| ≤ 1.5 LU; median duration ratio in
[0.90, 1.10]; median pitch shift within ±1.0 semitone; 0 loop clips; ≤ 1 bleed flag. Plus a short page at
NATIVE level (what the app would play): fine / problem, `broken`, `not her` — PASS if 0 broken and
≤ 1 not her. Response time (wall, incl. network) P vs the 2b paid A calls is REPORTED, not a gate
(latency work is closed; a large change is told to Zani).

## Ship (only on Zani's explicit yes after Stage 3)
Tag `pre-221b`. ONE commit, byte-identical to C except the model header: `FISH_MODEL = "s2.1-pro"` and
`"prosody": {"volume": V}` in `fish_tts()`; `GREETING_TTS_VER` v3 → v4 in `amadeus.html` AND
`dev/warm_greetings.js` (its own copy — a missed bump = every greeting misses, bugs.md 91 class);
`/health` and the startup banner name the real model; `dev/fish_payload_test.py` expects
`prosody == {"volume": V}` with mutants (no volume, wrong value, any `speed`, `normalize_loudness`), and a
test that the payload equals `arms_b2.request_for('P', …)`; all docs in the same commit.
Greetings (default answer to plan question 1): warm all 88 offline with `warm_greetings.js` on the paid
model with the app CLOSED, BEFORE the trial (cost stated from real bytes first; needs his yes).
Live trial, then his verdict. Revert: `git checkout pre-221b -- kurisu_fish_server.py amadeus.html
dev/warm_greetings.js dev/fish_payload_test.py` (the v3 greeting files stay on disk and hit again).

## Cost (real bytes, $15 per 1M UTF-8 bytes; every call counted as paid x1.5 by the guard)
Wallet $9.182010 (read 2026-10-01 00:11 BST; updated 2026-09-30 21:44 UTC). Step 0: 12–18 free calls,
real $0, guard ≤ $0.147. 2b: 22 paid + 32 free, **real $0.0983**, guard $0.369. Shared cap **$0.55**.
Stage 3: 8 paid, **real $0.0377**, cap $0.10 (a separate yes). The wallet lags; it is re-read next session.

## ERRATUM 1 (2026-10-01, written after Step 0 FAILED and BEFORE any Step 0b call; Zani chose "option 1")
Step 0 result (`step0_result.json`): `volume -8.5` → median −25.9 LUFS (effect 12.8 LU — Fish's volume is not
one-to-one), 3.9 LU too quiet; pitch +1.8 st. On copies level-matched to −14 LUFS the pitch shift is 1.1 st
(t2 1.59, f2 0.63): the estimator skips frames under an RMS floor, so a quieter clip is measured on fewer
frames; and its own draw-to-draw noise is ~3 st (#221b screens). **The ±1.0 st Step 0 gate was a PREREG flaw.**
Changes (`step0b.py`; free model only):
1. Pitch is REPORTED only, measured on level-matched copies. Voice identity is judged by Zani's "not her" box.
2. SELECT: C at −6.0 and −4.5 dB, 3 draws per line on t2 and f2 (12 clips). A least-squares line through
   (V, median LUFS) at −8.5 (Step 0), −6.0, −4.5 gives V* for −22.0 LUFS, rounded to 0.5 dB, clamped to [−8.5, 0].
3. CONFIRM on 6 FRESH clips at V* (3 per line), never the clips that chose it. PASS if |median − (−22.0)| ≤ 1.0 LU,
   max true peak ≤ −1.0 dBTP, duration ratio vs M in [0.92, 1.08]. Fail → STOP and ask Zani; no further correction.
4. `arms_b2.volume()` reads ONLY `step0b_result.json`; it is committed before any 2b call.
5. Cost: 18 free calls, real $0. The guard (every call as paid, x1.5) now totals Step 0 $0.098 + Step 0b $0.147 +
   2b $0.369 = $0.614, over the $0.55 cap. `synth_b2.py` will STOP on the cap; raising it needs Zani's yes,
   with the wallet re-read as evidence that the free model bills nothing. The real 2b cost stays $0.0983.
Everything else in this PREREG is unchanged.

## ERRATUM 2 (2026-10-01, written after Step 0b FAILED and BEFORE any Step 0c call; Zani chose "option 1")
Step 0b (`step0b_result.json`): volume −8.5 / −6.0 / −4.5 dB → −25.9 / −25.3 / −25.4 LUFS — a STEP of ~12.5 LU,
not a slope. Erratum 1's linear fit had no flat-response check; it clamped to 0.0 dB (= no prosody, −12.6 LUFS).
Hypothesis: a non-zero `volume` switches off Fish's `normalize_loudness`. `step0c.py` (free model only):
1. PROBE 4 settings × t2, f2 × 2 draws (16 clips): S1 `{"volume": -1.0}`; S2 `{"volume": 3.0}`;
   S3 `{"normalize_loudness": false}`; S4 `{"normalize_loudness": false, "volume": 3.5}`.
2. SELECT: a candidate has |median − (−22.0)| ≤ 1.5 LU, max true peak ≤ −1.0 dBTP, duration ratio vs M in
   [0.92, 1.08]; several → smallest error, a tie → fewer fields. None → if S4 − S3 = 3.5 ± 1.0 LU (a dial once
   normalisation is off), use `{"normalize_loudness": false, "volume": V}` with V = −22.0 − median(S3), rounded to
   0.5, clamped to [−10, +10]. Otherwise STOP (a flat response is detected by this rule, unlike erratum 1).
3. CONFIRM on 6 FRESH clips; the erratum 1 rules (level ±1.0 LU, peak, duration); pitch reported only. Fail → STOP.
4. The candidate C (and P) now carries the WHOLE selected prosody object; `arms_b2.prosody()` reads ONLY
   `step0c_result.json`. A ship must send exactly that object.
5. Guard bug fixed before any call: each stage's estimate is cumulative, so the running total is the LARGEST one
   (a sum double-counted Step 0). Step 0c fits the $0.55 cap ($0.245 + $0.180). 2b then needs ~$0.80 — Zani's yes
   first, with the wallet as evidence. Real 2b cost unchanged ($0.0983).

## ERRATUM 3 (2026-10-01, after Step 0c PASSED and BEFORE any 2b call; approved by Zani: "approve fixes 1–3 and the $0.80 cap")
- Step 0c PASSED: C = `s2.1-pro-free` + `{"volume": -1.0}` → −22.6 LUFS on 6 fresh clips (`step0c_result.json`).
1. **2b is the FIRST test of C, not only a confirmation of 2a.** 2a's M used Fish's loud default path; any non-zero
   `volume` switches to an undocumented quieter path that may process audio differently. The 2b rules are unchanged.
2. **Ship guard (added to the Ship section):** `dev/voice_221b2/level_check.py` — 2 clips on the PAID model with the
   shipped payload (~$0.009); FAILS unless the median is −22.0 ± 1.5 LUFS. Run before the live trial and whenever her
   level seems to jump. `fish_payload_test.py` pins `prosody == {"volume": -1.0}` exactly.
3. **Screens report the peak-to-loudness ratio (PLR)** of A and C (report only). Pre-2b check on saved clips: A 12.2 dB
   (n=16), C 12.5 dB (n=10) — her lip-sync input should match at an equal level.
4. **Guard cap for 2b raised $0.55 → $0.80** (cumulative estimate $0.425 + 2b $0.369 = $0.794; every call counted as
   paid, x1.5). Evidence: 42 free calls, wallet unchanged at $9.182010 after its 2026-10-01 09:11 UTC update.
   Real 2b cost unchanged: $0.0983. Stage 3 keeps its own $0.10 cap and needs a 2b pass.

## ADDENDUM 2c (2026-10-01, written after Stage 3 and BEFORE any 2c call; plan approved by Zani: "yes, approved, go ahead")
Stage 3 PASSED (8/8 fine), but Zani: clip 1 (t2) was "noticeably higher in pitch and tone" — measured +5.2 st vs today's
voice. s2.1 varies far more than s2-pro: today's voice −1.4…+1.3 st (n=32); s2.1 −1.1…+5.5, median +1.5…+2.3, 4 of 56
clips > +4 st. Zani: "too high" (1b); +0.5s per reply is acceptable (2a). Hypothesis: a lower Fish `temperature`
("controls expressiveness; higher is more varied") cuts the outliers. Risk: it may make her calm again (bugs.md 90).
Arms (`t2c.py`; free model; C + the Step 0c prosody; ONLY `temperature` changes): C7 = 0.7 (today's C), C6 = 0.6, C5 = 0.5.
**Part 1 (objective):** C6, C5: 3 draws × 16 lines; C7: 1 new draw × 16 lines + the 32 2b C clips (same config) = 48 per arm.
st = 12·log2(f0 / median f0 of today's A clips on the line). Stray = mean |st − the arm's median on that line|.
An arm QUALIFIES if ALL: stray ≤ 0.75 × C7's; one-sided permutation test (labels shuffled within each line, 5000, seed
2214) p ≤ 0.05; "high" clips (st > +4.0) ≤ C7's; screens: loops < 2, bleed ≤ C7's + 4, pauses ≤ C7's + 4.
Choice: C6 if it qualifies (the smaller change), else C5, else STOP and ask Zani (ship 0.7, or stop).
**Part 2 (his ear; only the chosen arm):** FRESH draws, chosen arm and C7, 2 × 16 lines. Blind sheet (seed 2214): 32 pairs +
4 flipped repeats + 4 C7-vs-C7 noise = 40, level-matched; boxes per clip: broken, not her, too high, too calm.
A broken / not-her / looping candidate clip = a loss. PASS if ALL: consistency ≥ 3/4; losses ≤ wins + 2;
"too calm" on T ≤ C7's + 1; "too high" on T ≤ C7's; "not her" on T ≤ 2; screens pass.
Pass → the ship plan uses that temperature (global: every emotion; the guard lines are in both parts) and `level_check.py`
uses 4 paid clips (~$0.02) to confirm level and pitch on the paid model. Fail → ship plan at 0.7, or stop — his choice.
**Cost:** real $0 (free model only). Guard (every call as paid, x1.5): Part 1 $0.775, cap $0.80; Part 2 ≈ $0.44, cap
$0.45 (corrects the "$0.30" said in chat). Each cap needs Zani's yes.

## OUTCOME (2026-10-04)
Shipped (tag `pre-221b`, commit `64eea81`): C at temperature 0.7 = `s2.1-pro` + `{"volume": -1.0}` — 2c rejected a lower
temperature. 74 greetings warmed at v4 (birthday pools deferred); 8 greetings > +4 st re-drawn (0 high left). Live trial:
Zani — *"I like her voice now. It's good."* **KEPT.** Total real spend 2b → ship ≈ $0.41.
