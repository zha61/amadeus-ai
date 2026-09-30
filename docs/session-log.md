# ⇢ START HERE — handoff for the next session (written 2026-09-07, last updated 2026-09-30, after #206 closed)

**Read CLAUDE.md first, then this block, then the newest entry below.**

## 🌐 2026-09-28 — Public snapshot: github.com/zha61/amadeus-ai
Public snapshot of the private working repo. Third-party character assets and probe results that embed game
script or private diary text are excluded.

## ⏭️ NEXT SESSION (fresh, Zani's choice 2026-09-30): #221 — her tsundere/flustered VOICE sounds too calm
Read backlog #221 in full, then plan the blind A/B (fixed Japanese lines from `fish.log`; A current / B rule-15/32
rewrite / C = B + per-sentence re-anchor; check V3's pause problem; tsundere AND flustered; state Fish credit first).
CLAUDE.md 53 applies. Also open, not in his order: #222, #223 (hands-free stuck — needs the DevTools line when it
happens), #224 (prewarm, record only). **Not pushed:** all 2026-09-30 commits — ask him before pushing.

## ✅ 2026-09-30 — #206 CLOSED, zero code (backlog #206, new #224)
RAG readiness gate WORKS at 3/3 new cold boots (embed ~3s, ready in 4.5–6.3s; the 16.4s original did not recur).
The renderer prewarm is aborted at the 4s cap at every cold boot and shows no measurable benefit → backlog #224
(record only; latency work is closed). Diary index: no error at any boot; `diary_index_check.py` after the 20:51
close → 1 missing (that entry), exit 3 — expected.

## 🎤 2026-09-30 — #205 SHIPPED and LIVE-CHECKED (bugs.md 97). No rebuild.
The hands-free gate also drops a Whisper repetition loop: segment compression ratio > 2.4, or a 2–6 word group
repeated 4+ times. Nothing new on screen. **Live check (Hands-Free ON):**
1. Say 3 normal sentences — she replies to each. 2. Say one long sentence (~20s) — she replies.
3. Say "a great deal" 8 times IN ONE BREATH (a 900ms pause splits it) — no reply, status back to "Listening…".
4. Close. Read `whisper.log` (`compression=`, `segments=`) and `renderer.log` (`gate discard: reason=`).
Revert: `git checkout pre-205 -- amadeus.html kurisu_whisper_server.py` (relaunch only).
✅ **LIVE-CHECKED 2026-09-30 20:07–20:43 (3 launches): 0 false positives.** 11 real utterances reached her (ratios
0.33–1.74, incl. ~20s monologues of 6 segments). One real Whisper junk output was discarded (20:39:06, "you currently",
74 segments, ratio 10.89 — `reason=logprob` fired first; the ratio check would also have). **Step 4 cannot be done by
voice:** Whisper transcribed 8 SPOKEN repeats as one "a great deal" (ratio 0.60) — it de-duplicates real speech; the loop
comes only from non-speech. The loop case rests on `dev/whisper_gate_test.js`. Do not ask Zani to repeat step 4.
Found during the check, NOT caused by #205: hands-free (RMS) got stuck twice → backlog #223 (evidence + DevTools line).
**Order Zani set (2026-09-30):** #205 → #206 → #221. New: backlog #222 (held rescue text after a discard; recorded only), #223.

## ✅ 2026-09-30 — #217 SHIPPED and LIVE-VERIFIED (bugs.md 96). No rebuild.
✅ **LIVE-VERIFIED 2026-09-30 19:52** (Zani's DevTools screenshot): the same 3 facts in the same order before and after
`_memoryRefreshActive()` (it prints `undefined` — no return value, not an error); `factsStatus()` → `3 stored (3 active
this session)`; `renderer.log` from 18:50:49Z has no WARNING/ERROR line. **Live check used (closed):**
A memory-panel add/edit/delete now re-selects her facts with the boot ranking (`_memoryRefreshActive` → `initFacts`).
Her boot prompt is byte-identical (tested against `b8e929e`). Zani chose #217 before #221 this session.
**Live check (no panel use — a panel change queues a "she notices" note and writes her memory):** relaunch; in DevTools
1. `_factsActive.map(f=>f.fact)` → note the list. 2. `_memoryRefreshActive()`, then step 1 again → the SAME list.
3. `factsStatus()` → `3 stored (3 active this session)`. Then read `data/logs/renderer.log` for errors.
The store holds 3 facts, so the live check cannot show the >20 effect — the offline test proves it.
Revert: `git checkout pre-217 -- amadeus.html` (relaunch only).
**Next:** #205 → #206 → #221 (Zani's order).

## 🎙️ 2026-09-30 — NEW from Zani: her voice sounds too calm when she is tsundere/flustered (backlog #221)
He said: too calm, no fluster in the voice; no English words; unsure if tsundere only or flustered too. Nothing changed.
**Strongest lead (H1):** Fish S2 applies a tag only "until the next tag or end of the sentence", and `/speak` sends ONE
direction at the start — sentences 2+ are undirected. V3 (July) removed the per-sentence re-anchors while fixing pauses.
Next: reviewed plan → blind A/B arms (current / rule-32 rewrite / + per-sentence re-anchor) → his ear → live trial.
**2026-09-30: Zani chose #217 first (now shipped).** Order: #205 → #206 → #221.

## ✅ 2026-09-30 — #218 SHIPPED and LIVE-VERIFIED (bugs.md 95). No rebuild.
✅ **LIVE-VERIFIED 2026-09-30 (2 launches).** Launch 1 (4 turns, close 19:32): no `diary index skipped`, no `/index-diary` at close, `diary_index_check.py` → 1 missing (the new 19:31 entry), exit 3 — as expected. Launch 2: `rag.log` 19:33:27 `upserted 1 new entries`; check → **0 missing**, 69 documents, exit 0. **In launch 2 the diary was read from `000118.ldb`** (LevelDB had compacted it) — the `.ldb`/Snappy path, added during the build, was needed on the very first real use.
The close no longer indexes the diary; the boot index reconciles it. **Live check used (closed):**
1. Launch, chat, close normally. `renderer.log`: no `diary index skipped`; `rag.log`: no `/index-diary` at close;
   `python3 dev/diary_index_check.py` → exactly **1** missing (the new entry) — EXPECTED.
2. Launch again (closing after the greeting is fine). `rag.log`: `upserted 1 new entries`;
   `diary_index_check.py` → **0** missing.
Revert: `git checkout pre-218 -- amadeus.html kurisu_rag_server.py` (relaunch only).
**Next:** #217 → #205 → #206. New: backlog #220 (quit during the boot index; untested, low priority).

## ✅ 2026-09-29 (evening) — #219 SHIPPED and LIVE-VERIFIED (bugs.md 94, log noise). Rebuilt.
✅ **LIVE-VERIFIED 2026-09-29 18:44–18:47** (4 text turns, normal close): no deprecation line after the newest `main.log` header; `[unload]` marker then 4 `[BootVideo] … (unload teardown)` lines; no `BGM track not found`; `[Perf]` lines carry `INFO`. No WARNING/ERROR line occurred live, so that level rests on the real-Electron test (check 9).
**Live check used (kept for reference, closed):** relaunch → send one message → close normally. Then read, AFTER the newest
`main log start` header in `data/logs/main.log`: no `'console-message' arguments are deprecated` line. In
`renderer.log`: an `[unload] releasing audio/video …` line, no `BGM track not found` after it, the boot-video
lines after it end in `(unload teardown)`, and the `[Perf]` line still carries a level.
Revert: `git checkout pre-219 -- main.js amadeus.html && npm run build`.
**Next, in Zani's order, one at a time with a reviewed plan and his yes:** #218 → #217 → #205 → #206 (ask him
when he has done 3 cold boots). **The push of `138cb2f` was blocked by the auto-mode check** — Zani runs it himself.

## ✅ 2026-09-29 — bugs.md 93 LIVE-VERIFIED (log sink works; one session). New from the logs: backlog #218, #219.
✅ **LIVE-VERIFIED 2026-09-29 18:18–18:21** (one session, checked by reading the files): all 6 logs created with spawn headers; whisper output arrives after ~8s of imports; one reply produced a renderer `[Perf]` line, the full fish `[TTS]` chain and rag retrieval lines; 0 LipSync peak/ticker lines kept; at close the Ollama log shows the diary (18:20:51) and summary (18:20:58, 93 tokens) and main.log has no facts-close timeout (1 exchange → skipped-short, as designed).
**Next session (fresh):** #219 (1-line fix), #218, #217, #205 (repetition check), #206 (read Ollama log after 3 cold boots).

## (done) 2026-09-27 (late night) — bugs.md 93 SHIPPED (log sink).
1. Relaunch. `ls data/logs/` must show fish, http, rag, whisper, main and renderer `.log`, each server file
   with a `=== … spawn <name> pid … ===` header.
2. Send one message. `renderer.log` must hold a `[Perf]` line; `fish.log` must hold `[TTS]` lines.
3. Close normally. `main.log` must hold the diary / summary / facts-close lines.
Revert: `git checkout pre-203 -- main.js kurisu_rag_server.py amadeus.html && npm run build`.
**Then start a FRESH session** (Zani's choice: this session was long). After that: #217 (small), #206
(read the Ollama log after 3 cold boots), #205 (repetition check on Whisper transcripts — confirmed broken).

## ⭐ 2026-09-27 (night) — #216 SHIPPED (fact age notes + renewal). Nothing to check today.
**Her prompt is byte-identical until a fact turns 30 days old — about 2026-10-27.** On the first launch after
that date, run `dumpSystemPrompt()` and look for `[learned over a month ago — it may have changed]`, then ask
Zani how she sounds (CLAUDE.md 53). Revert: `git checkout pre-216 -- amadeus.html` (relaunch only).
The "confirmed" field was measured and rejected — do not re-propose it (PREREG_216). Next open items: #217
(small), then the audit order: #203+#204 (IN PROGRESS, same session) → #205 (Zani confirmed he did NOT say
"What a great deal" — the gate let a hallucination through) → #206.

## ✅ 2026-09-27 — bugs.md 92 SHIPPED and LIVE-VERIFIED, all 3 steps ("she sounds the same").
✅ **LIVE-VERIFIED 2026-09-27 ~17:30 (steps 1–2), Zani's DevTools screenshot.** `factsRuns()`: row 0 `idle`, 746 chars, eval 51, stop, n=2, ok, 1939ms; row 1 `close`, 1304 chars, eval 21, stop, n=1, ok, 1306ms. `factsStatus()`: 3 stored, 3 active. **The idle pass ran AND stored** — so the ten empty weeks were most likely "ran and saw nothing", not "never ran". Step 3 (how she sounds with the facts block) is his ear — pending his report.
**What shipped:** once per session, at close, she extracts facts from the whole session (backlog #202).
Rebuilt. Tag `pre-202`. Tests: `node dev/facts_close_test.js` (29 + 3 mutants).
**Live check for Zani (one session):**
1. Launch. Tell her 2 durable facts (for example, a dated plan and a new hobby). Close the app normally.
   The SAVING screen should last ~3–6s longer than before.
2. Relaunch. In DevTools run `factsRuns()` → the last row must be `trigger close`, `outcome ok`, `n ≥ 1`.
   Then `factsStatus()` → the facts must be listed.
3. Talk to her. The new "THINGS YOU HAVE LEARNED ABOUT ZANI" block is in her prompt for the first time
   ever. **His ear decides** (CLAUDE.md 53). He can delete facts in the memory panel.
**Prompt backup:** `dev/prompt_snapshots/` holds a byte-exact copy of SYSTEM_PROMPT (identical to
`pre-q0-ship` and `pre-202`) with a one-line check and restore steps.
**Revert:** `git checkout pre-202 -- amadeus.html main.js preload.js && npm run build`, AND in DevTools
`localStorage.removeItem('amadeus_facts_v1')` (old code injects stored facts too).
**After a week of use:** read `factsRuns()` — the `idle` rows finally answer whether the in-session pass
runs and what it finds.
**Audit results (same day) still stand:** 15 WORK, 3 BROKEN (#202 now fixed, #201, #205), 1 latent (#203),
11 UNKNOWN; 7 of them need a log sink (#204). Next after this check, in the order shown to him:
#203+#204 → #205 (ask him if he said "What a great deal") → #206 (zero code). Ask before each.
Separate small follow-up noticed: 1 of 3 replay runs dated an exam 2024 instead of 2026 (event_date year).
**Rules still in force:** no gemma4 while the app is open (CLAUDE.md 37); copies go to the scratchpad;
display frozen (CLAUDE.md 51); #180, length and latency closed.

## ✅ 2026-09-27 — ALL THREE LIVE CHECKS PASSED. Greeting-cache fix (bugs.md 91) LIVE-VERIFIED.
**Results 2026-09-27:** Check 1 (boot video, bugs.md 84) ✅ passed. Check 3 (P1 voice path) ✅ passed — a
hands-free turn logged `[Perf] voice-rms … stt 4421`. **Check 2 (bugs.md 83) ✅ passed ON ZANI'S REPORT:**
he talked hands-free for more than 10 minutes and it stayed on. That session is not in the retained Ollama
log, which starts 2026-09-25; the fix has been live since 2026-09-07, so an earlier session counts.
**Closed. Do not ask him to re-run it.**
**Shipped 2026-09-27 — bugs.md 91:** the greeting audio cache never hit (read path lacked `data/`). Fixed
in `amadeus.html`, no rebuild. ✅ **Live-verified 13:23** — no translate call and no file write after reveal.
**Found, NOT fixed — backlog #201:** Silero VAD has never loaded (onnxruntime 1.22.0 in the bundle vs
1.17.3 vendored files); every hands-free session runs on the RMS fallback. Needs his decision.
Steps used for the checks (kept for reference only — all three are closed):
1. **Boot video (bugs.md 84)** — relaunch once; it must play clean to the end.
2. **Hands-Free ON, one session over 10 minutes (bugs.md 83)** — it must not end while he talks.
   Hands-Free OFF is a different code path and does not test this fix.
3. **The same session verifies the P1 voice path** — each `[Perf]` console line must read `voice`
   (not `text`, bugs.md 80) and show a number for `stt` (not `—`).
Then `latencyStatus('voice')` and `latencyDump()`. **Do NOT run `latencyReset()`** — it deletes the
19 recorded text turns, and the voice filter already ignores them.
Pre-checked 2026-09-22: `npm run check` 11/11, `hf_boot_test` 17/17, `perf_trace_test` 45/45,
`PERF_TRACE=true`, Fish API credit **$9.60** (~1,950 replies).
⚠️ **Dump filename trap (backlog #200):** `~/Downloads/amadeus_perf.json` already holds the
2026-09-06 dump (n=4, text). The new dump will probably be saved under another name, but the console
still prints the old path. Take the NEWEST `amadeus_perf*.json` and check its `capturedAt`.
**Repo:** `fix-180` was fast-forward merged into `main` (2026-09-22 22:21) and deleted. HEAD `dcaa559`.
**Pushed 2026-09-26 with his yes:** `main` (49 commits, fast-forward, `--atomic`) and all 37 tags are on
GitHub, verified ref-by-ref. The repo is PRIVATE (anonymous API → 404). 32 result files in
`dev/canon_arms/` hold diary excerpts in `rag_block` — **if the repo is ever made public, remove them
from HISTORY first; a delete commit is not enough.** Three docs still
said "branch `fix-180`" (CLAUDE.md, this file, backlog #180). **Fixed 2026-09-26 with his yes** — they now
name `main` and tag `180-closed`. Dated history lines that mention the branch were left as written.
**Ranked list shown to him 2026-09-27:** (1) the silent-fallback audit above — CHOSEN. (2) #172 full-stack
RAM (gemma4 4.17 GiB and bge-m3 0.57 GiB measured 2026-09-27; Electron + 3 Python servers remain; ~2 min
with the app running). (3) #173 Study Mode brake — only if he uses Study Mode (ASK), and MEASURE first.
(4) #11 topic-tagged diary recall. Then, waiting on his decision: #183/#161 (do NOT apply #183 as
written — its sample came out softer, and he reverted Q0 for sounding too calm), #191 (adds to the
screen, CLAUDE.md 51), #197/#198 (touches her voice — live trial only), #201 Silero (downloads files),
#200, #169.

## 🔚 2026-09-22 — BACKLOG #180 (her openers / her "heat") IS CLOSED. Do not re-open it.
Seven weeks, 13 arms, 5 mechanism families, 2 blind A/B tests, 1 live trial — **nothing shipped.**
Q0 reached the app on 2026-09-19 and Zani reverted it on 2026-09-22: *"way too calm"*, *"I like her
voice before"*. `amadeus.html` is byte-identical to tag `pre-q0-ship`, the prompt he has always liked,
and he confirmed she sounds right again. See **CLAUDE.md standing instruction 4**, bugs.md 90 and
CLAUDE.md 53 (for tone, metrics can only reject; his ear in a live trial is the only gate).
`main` keeps every tool, arm, pre-registration and result (branch `fix-180` was merged and deleted 2026-09-22; tag `180-closed`). **Do not restart this work.**

## 🔒 TWO STANDING INSTRUCTIONS FROM ZANI — these bind every session
**1. Write to him in ASD-STE100 Simplified Technical English.** Sentences to 25 words, active
voice, one instruction per sentence, same word for the same thing, lists for multiple items.
**Hardest on technical content** — measurements, root causes, trade-offs. That is exactly where
it keeps getting dropped. It applies to how you write TO HIM, never to Kurisu's dialogue.

**2. DO NOT CHANGE HOW HER TEXT AND AUDIO APPEAR ON SCREEN (2026-09-07).** The word-by-word
reveal timed to her voice is finished work. *"The Amadeus before was great."* Frozen: the
subtitle reveal and its timing, the `...` placeholder, the thinking dots, when text appears
relative to her voice, and how audio is delivered. **Already rejected — do not re-propose:**
streaming her text as she writes it, and the P4 thinking indicator (bugs.md 81/82).
**This rules out #188 / P3 streaming TTS as designed** — per-sentence synthesis breaks the
audio-duration sync (bugs.md 6).
**HE STILL WANTS HER FASTER, without losing quality.** Everything below the display layer is
open. Ranked list is in the "what next" section below. **The top item is NO LONGER the translate
step — that closed on 2026-09-07 with all four arms measured and rejected (#196).**
**⛔ #176's LENGTH INSTRUCTION: MEASURED, IT WORKS, AND ZANI DECLINED IT (same day).** One
prompt line took her ≤8-word replies from **0.0% to 50.0%** (canon 50.8%) and cut **~750ms/turn**
(generation −31.5% tokens, translate 902→675ms). He then said, unprompted: *"I think now the way
she talks is fine, like the sentence length."* **Do not ship it. Do not re-open the LENGTH gap as
a defect** — see CLAUDE.md standing instruction 3 and backlog #176. Her VOCABULARY and PHRASING
are a separate axis and are NOT covered by that decision.
**⚠️ THE PER-TURN RAG BLOCK (#160) — the +533ms is REAL but it is NOT an available saving.**
Decomposed the same day, n=8 on the real captured prompt: the block is 414 tokens = 154 static
header tokens + 257 retrieved-line tokens. **Moving the static headers into the cached system
message saves only +37ms.** The sizeable lever is **trimming retrieved diary entries to their
first sentence: +160ms** — and that cuts the emotional-continuity detail bugs.md 69/71/72 were
spent getting right. **Cost is NOT linear in block size** (142 header tokens → 37ms; 213 diary
tokens → 268ms) and there is an ~84ms floor. **Do not quote +533ms as a saving.**
**So there is no large quality-free speed win left in the app.** Every remaining lever costs
something Zani has already said he values: her length (declined), her memory (#160), or her
register (#196/DeepL).
🛑 **AND HE STOPPED IT.** Shown that table, he said **"stop here."** **The latency effort is
CLOSED. Do not reopen it unprompted.** Nothing was shipped in this whole session — `amadeus.html`,
`main.js` and `kurisu_rag_server.py` are byte-identical to `04d5fda`. The only runtime change all
session is one reconciled COMMENT in `kurisu_fish_server.py`. **If he raises slowness again, ASK
what feels slow before proposing anything** (the P4 lesson, bugs.md 81/82).
**Still open and waiting on HIM, unrelated to speed:** the P1 VOICE path (**verified live 2026-09-27**) ~~has never been verified
live~~ (every recorded turn is `kind:'text'`; needs an evening of hands-free use then
`latencyStatus()` + `latencyDump()`); backlog #183 the diary rewrite is parked mid-flow; and
backlog #161 needs his decision on the old clinical diary entries.

⭐ **THE TOP OPEN ITEM IS NOW HER OPENER CRUTCHES (#180), re-measured 2026-09-12, n=30.**
**26 of 30 flirty replies (87%) open with one of two phrases.** `"Don't"` **36.7%** against
canon's 1.9%; `"W-what"` **33.3%** against canon's 0.1%, plus 13.3% of `"Wh-what"` — the same tic
in a different spelling, so **match the FAMILY or a scorer will report a win that did not
happen.** Only 8 distinct first words in 30 replies. **bugs.md 77 did not hold.**
**This axis is explicitly still open** — CLAUDE.md standing instruction 3 froze her LENGTH, not
her phrasing. Fix it with a RULE FOR FORMING, never another list (CLAUDE.md 45), and check the
replacement against CLAUDE.md 43 before shipping. Full method in backlog #180.
**Recommended as a FRESH session** — it needs the full prompt-measurement loop and Zani's ear.
🔄 **UPDATE 2026-09-12 (late): #180 IS IN PROGRESS on branch `fix-180`. Nothing shipped.** That
26/30 ran with RAG DOWN (bugs.md 85); with RAG verified up it is 28/30. Five arms measured — the
best (D) cuts the crutch to 9/30 but opens 16/30 replies (corrected from 18) by echoing his word as a question. Review
found the emotion tag, written BEFORE the text, picks the opener (`[flustered]`→"what" 65%,
`[tsundere]`→"don't" 82%). **Read backlog #180's top block and the 2026-09-12 session entry
below before running anything.** `main` is still `2061a0e`. The hand-started RAG server was stopped
at session end — start it again (`python3 kurisu_rag_server.py`) before any RAG-on arm.
**2026-09-13: Zani came back and chose to continue in the same session. He then asked for a plan
review, all flaws fixed, and approved Stages 1–5 including arm G. The decisions below are ANSWERED;
the pre-registration is `dev/canon_arms/PREREG_180.md`.**
*(#180's closure is stated at the top of this handoff — the block below is the older #180 context.)*
**LATEST (2026-09-19): #180 has now tried FIVE mechanism families; none passed. Zani's goal (variety +
heat with pervert/idiot/dummy on teasing lines, soft on sincere, none when sad — kurisu-personality.md)
hits a gemma4 ceiling of ~4/17 teasing replies with a name (arm TQ, which also shortens her). The
variety gains (B hygiene, Q0) are real. `amadeus.html` is STILL unchanged; branch `fix-180`, tag
`180f-screen`. Next step is Zani's choice — options in the 2026-09-19 entry below.**
**THEN STOPPED AT STAGE 2 by the pre-registered tree (no candidate passed). Zani then asked for a
review, a chosen next step and a reviewed plan: the second screen is `dev/canon_arms/PREREG_180b.md`.
IT ALSO STOPPED (Stage B, no arm passed). Nothing shipped; `amadeus.html` is unchanged. Zani's
choice is needed next — options are in the latest session entry and backlog #180.**
**(Answered) Zani paused for the night with THREE DECISIONS OPEN:**
1. Approve the revised plan, Stages 0–5 (pre-register bars → tag diagnostic G → F / F+G → holdout
   confirmation paired on seeds → daily + multi-turn guards → blind A/B sheet)?
2. May arm G (emotion tag at the END of the reply) be tested? Diagnostic only; shipping it changes
   the output format `parsEmo` reads and needs a tag-consumer audit.
3. Continue in a fresh session? (Recommended — this one was long.)
The full plan, the bars, and the costs are in the 2026-09-12 session entry and backlog #180.

⚠️ **backlog #169 resolved differently: `OLLAMA_FLASH_ATTENTION` was never in effect.** main.js
sets it, but main.js only spawns Ollama when it is not already running, and Ollama runs as
`Ollama.app` under launchd. The live `llama-server` shows `--flash-attn auto`. There was no
unverified risk — there was dead configuration. Decide: delete the lines, or set them via
`launchctl setenv` (as main.js already does for `OLLAMA_ORIGINS`) and then re-run the check.

✅ **AFTER the stop, he asked for two improvements and both shipped — bugs.md 83 and 84**
(`amadeus.html` only, no rebuild). ~~NEITHER IS LIVE-VERIFIED.~~ **2026-09-27: 84 verified; 83 still open.** He needs to (1) hold a
hands-free voice session longer than 10 minutes — it should no longer cut out, and this finally
exercises the untested P1 voice path — and (2) relaunch once and watch the boot video play clean.
Tests: `node dev/hf_boot_test.js` (17). Revert: `git checkout pre-196 -- amadeus.html`.

The conversation that produced the recent work is CLOSED — nothing lives in chat
history. Everything you need is in the docs.

## State of the project
Working and **live-verified**: boot video, greeting continuity, temporal memory,
hands-free voice, Study Mode, camera vision, D-Mail, birthday event, memory panel,
plus bugs.md **66** (lip-sync node leak) and **67** (truncation guard).
Also live-verified Aug 23: bugs.md **68** (Zani saw prefill drop from ~1569ms cold to
~850ms, and held a full conversation on the new layout with no register problem traced
to it) and bugs.md **69** — **he pressed Reset and confirmed the new diary entry "looks
like a person more than before."** That is one entry, not a statistic, but it is the
outcome the fix was for and it matches the measured direction (17% → 3%, p=0.097).
Also live-verified Aug 26: bugs.md **70** (truncated long-term memory), **71** (long-term
memory written as a case file) and **72** (the memory froze forever at the 50-entry diary
cap). **Zani's FIRST test attempt failed — that is how 72 was found**, and it showed 70 and
71 had been unreachable on his machine all along. After 72 shipped, his second attempt
passed all three: watermark `50` → `c8e364f1b6441457`, summary ending in a complete
sentence, in first person, no case-file vocabulary. 72's verification is a binary state
change and is solid; 70 and 71 rest on one sample each plus the offline figures
(63% → 0% and 97% → 7%).
Shipped Aug 26, **no rebuild — relaunch picks all of these up**, none yet live-observed:
bugs.md **73** (fact extractor discarded every fact it found 33% of the time), **74** (that
extractor held the GPU up to 9.66s with no brake), **75** (bge-m3 unloaded after 5 min, so the
first message of a session stalled the GPU 812ms — Zani's "2s lag" report), **76** ("Don't get
the wrong idea" in 37% of replies because the prompt quoted it twice — now 3%).
~~Ask Zani how 75 and 76 feel~~ — **both answered on Sep 3, and neither answer was the expected one.**
**76:** the catchphrase it removed came BACK, because she had already written it into a diary entry
and the diary is injected into every prompt (backlog #184). A prompt fix does not hold if the
phrase survives in memory. **75:** Ollama upgraded itself to 0.33.2, where the default `keep_alive`
is 30 minutes, not 5 — so that fix is redundant on this version and load-bearing again the moment
the default moves back. **Confirm it via `/api/ps` `expires_at` with the app running, never by the
absence of the symptom.**
Repo clean. **Run `npm run check` before EVERY relaunch** — it now parses `main.js`,
`preload.js` and `preload_call.js` too (backlog #170, Aug 26), so the hand-run
`node --check main.js` workaround is retired. `npm run check:selftest` after editing
`dev/check.js` or upgrading Node — it is 7/7 and covers the new checks. Unit tests for
the summary guard: `node dev/trim_summary_test.js` (21/21).
Dev helpers in DevTools: `dumpLastTurn(n)`, `perfStatus()`, `truncStatus()`,
`factsStatus()`, `relStatus()`, `dmailStatus()`, `dumpSystemPrompt(n)`,
`dumpStagePromptsToFile()`, **`latencyStatus()`/`latencyDump()`/`latencyReset()`** (Sep 4,
backlog #186 — the presence trace), and **`rewriteClinicalDiary({apply})`** (Sep 3 — dry run by default,
backs up to `amadeus_diary_bak_<ms>` before writing; see backlog #183).
**Offline toolchain (Sep 3):** `dev/canon_likeness.py --validate` (run FIRST — it prints the
noise floor: under ~5 words at n=30 is not a difference), `dev/canon_gap_probe.py` (calls gemma4 —
never with the app open), `dev/prompt_lint.py` (run before EVERY prompt edit), `dev/dedupe_diary.py`
(app CLOSED). Full descriptions in CLAUDE.md → *Voice / memory measurement toolchain*.

## Do these first if asked "what's next"

**Everything below is DONE. The repo is clean and nothing is half-applied — but P1 (#186)
is shipped-and-UNVERIFIED, unlike everything under it. Read its bullet before assuming.**

### ✅ RESOLVED same day — the voice outage of Sep 6 (backlog #191)
Fish Audio **API** credit hit -$0.05 and `/speak` returned `402`, so `ttsSpeak` fell back to the
silent text reveal: she replied normally with no voice and **nothing on screen said why**.
Zani topped up +$10 the same evening. **Verified working end-to-end at 20:55** — `/speak` returned
30,092 bytes on `s2-pro` with his original `reference_id`, translate 515ms + fish 826ms.
Balance **$9.95**, cumulative top-up $15.00 (~2,000 replies at ~$0.0049 each). No code changed.
**Three things to remember, because each one cost time today:**
1. **Fish has TWO wallets.** The ~9,000 shown in the web UI is PLATFORM credit; the API bills
   API credit, and the 402 message says so explicitly. Read the real one:
   `GET https://api.fish.audio/wallet/self/api-credit` with the Bearer key from `config.json`.
2. ~~A cached greeting can mask the outage — or fail to.~~ **WRONG, corrected 2026-09-27 (bugs.md 91):**
   the cache never hit, so no greeting could play on a dead balance. **Judge by the REPLY** still holds.
   In the event Zani's greeting was silent too: `pickFresh()` deliberately avoids recently-heard
   greetings, which are exactly the cached ones, so it biases toward a cache MISS — and a miss is
   synthesised through `/speak`.
3. **#191 is still OPEN as a design fix.** A 402 is permanent until paid; a timeout is transient;
   the UI treats them identically and shows nothing. Worth surfacing "voice unavailable".

### ❌ P4 SHIPPED, BROKE HER REPLY TEXT, AND WAS REVERTED (Sep 7) — bugs.md 81 then 82
`amadeus.html` is back at `pre-p4` (`dd9fd97`). **The app is in its pre-P4 state and that is the
state Zani wants.** Do not rebuild P4 without him asking.
**What broke:** `playSyncedAudio` never sets `.on` on `#subtitle` — it writes text and relies on
`sendMsg` for visibility. P4 made that `sendMsg` line conditional, so on every normal reply the
container stayed `display:none` and **her words never rendered.**
**How it got through:** `npm run check` green, 22 unit tests green, both mutants caught. Every
test asked "does my indicator behave?"; none asked "are her words on screen?" → CLAUDE.md **50**.
**And the feature was unwanted anyway.** Zani: *"there's always three dots anyway... the Amadeus
before was great. This change is unnecessary."* The `...` placeholder already did this job.
**I inferred the problem from a latency number instead of asking whether the wait bothered him.**

### ⇢ DIRECTION UPDATED Sep 7: HE IS A TEXT USER, NOT A VOICE USER
**"Now I mainly focus on using text, we can work on voice in the future."** The Sep 4 presence
plan was scoped around voice because the Jarvis framing implied it — **I never asked how he
actually uses her, and that was my error.** Two of the five items are voice-only and are now
DEFERRED, not cancelled: **P2 barge-in (#187)** and **P5 semantic turn detection (#190)**.
**Re-ordered for a text user, on the n=19 evidence below:**
1. ❌ **"Show her text as she writes it" — REJECTED BY ZANI, Sep 7. Do not re-propose it.**
   It would have cut the perceived wait ~4.8s → ~1.0s for free, but it makes her whole reply
   readable before she speaks it. **He wants the reveal exactly as it is** — the line should land
   when she says it. That is a character decision, not a performance one, and it outranks the
   4.8s. The full design (dimmed draft + bright highlight tracking her voice) is in this
   session's entry below if it is ever revisited.
2. ❌ **P4 (#189) — SHIPPED AND REVERTED Sep 7.** Broke her reply text; also unwanted. See above.
   **Ask before touching the subtitle at all.**
3. ✅ **THE TRANSLATE STEP — CLOSED 2026-09-07. All four arms measured and rejected.**
   It is **1022ms** and **77% of it is decode** at ~27ms per output token, so nothing about the
   prompt touches it. DeepL is 630ms faster and fails register on every axis AND invented a fact
   (君の勤務時間 for "your hours"). `gemma3:4b` is 7ms different against a ±100ms noise floor.
   `num_predict` is not a lever (0/30 truncated). Overlap cannot run, because `llama-server` is
   `-np 1` and a concurrent request queues. **Do not re-run any of these** — full numbers in
   backlog #196 and the Sep 7 (later) entry below.
   **The "+0.57s KV penalty" was wall time of a 3-token request. It is +2ms.** Do not reason
   from the old figure.
   **The only thing left that cuts translate is #176** — decode scales with her reply length, so
   halving it is worth ~390ms/turn, as a side effect of a change wanted for character reasons.
4. ❌ **P3 streaming TTS (#188) — BLOCKED by rule 51.** Per-sentence synthesis breaks the
   audio-duration subtitle sync (bugs.md 6). Do not start it without a fresh decision from him.
5. ⭐ **THE NEW TOP ITEM — the per-turn RAG block costs +533ms of prefill, EVERY turn (#160).**
   Found 2026-09-07 while measuring translate. Same real captured prompt, only the RAG block
   held constant vs varied: **84ms vs 616ms**. gemma4 prefills at ~730 tok/s, so a ~431-token
   block that changes every turn is ~590ms that can never be cached. **Message order cannot fix
   it; only a smaller block wins.** Below the display layer, so rule 51 does not block it. It
   touches retrieval and therefore her voice — measure with `dev/canon_likeness.py --validate`
   then `--compare`, noise floor W≈5.0 words at n=30. The 744-char diary pair is the bulk (#13).
   **This is bigger than anything translate had to offer, and it costs no quality if the block
   is trimmed carefully.**
6. **Prefill / prompt budget (#156, #160)** — 894ms median on a ~4,156-token prompt, and EXAMPLES
   is 31% of `SYSTEM_PROMPT`. Below the display layer, so it is allowed. Touches her character,
   so measure register before and after (CLAUDE.md 43/45/46).
7. **First-message lag — DIAGNOSED, NOT MEASURED (Sep 7).** Zani reports lag on the first message
   of a launch. His data shows turn 1 prefill 1594ms vs 855-1004ms after. **But the trace does
   not capture Ollama's `load_duration`**, so the split between model load and prefill is
   unknown. `prewarmOllama()` exists to absorb this, and boot waits for it with
   `Promise.race([prewarmOllama(), delay(4000)])` — **at most 4 seconds**, while the prewarm's
   own comment says a first load can take ~10s. **Adding `load_duration` to the trace is one
   line and would settle it. Zani said to leave it for now.**
8. **CLAUDE.md 36 has an inaccurate claim, found Sep 7, NOT fixed.** It says the prewarm is
   "awaited to completion, so nothing overlaps playback". `Promise.race` does not cancel the
   loser, so a prewarm slower than 4s keeps running DURING the boot video — the exact condition
   bugs 60/63 exist to prevent. Verify before trusting that line.

### ⇢ THE PRESENCE DIRECTION (set by Zani, Sep 4)
His north star is **Jarvis-style real-time support, with Kurisu's personality, voice and
appearance unchanged.** He chose **presence before awareness**. Presence is a LATENCY problem.
Scope lives in backlog **#186–#190** (P1–P5); read that section before proposing anything here.
- 🔧 **bugs.md 80 (Sep 7) — the tap-to-speak mic path was NEVER instrumented.** Zani had a full
  spoken conversation and `latencyStatus('voice')` said "no turns recorded yet". Two causes, both
  fixed: the mic button runs TWO paths (Hands-Free ON = Silero session, instrumented; OFF =
  tap-to-record, **not** instrumented — and OFF is the default), so spoken turns were logged as
  `kind:'text'`; and `latencyStatus(kind)` matched by exact equality, hiding `voice-rms` and
  `voice-tap`. **Needs a fresh voice session to verify — his earlier turns are unrecoverable**
  (they are in the ring as `text`, with no `stt`). → CLAUDE.md 48(c)/(d).
- ✅ **P1 (#186) — LIVE-VERIFIED on the TEXT path (Sep 6), n=4.** It records, closes every turn,
  and two independent clocks agree to 9ms (renderer TTS round trip 2859ms vs the Fish server's
  own 1430+1420=2850ms). Its first run also found a defect in ITSELF — `rag: null` on text turns,
  now bugs.md **79**.
  ~~STILL UNTESTED LIVE: the VOICE path.~~ **Verified 2026-09-27** (`voice-rms`, `stt 4421`). All four turns were `kind:'text'`, so `stt` has never
  run in the real app — and voice is where CLAUDE.md 48(b) bites. **The next run must include
  hands-free turns.**
  **What Zani has to do, and only he can do it: use her normally for an evening, voice included.**
  Then `latencyStatus()` AND `latencyDump()` in DevTools — **send the dump file, not just the
  medians** (bugs.md 77b: a summary hid two 900-second outliers once already).
  **n>=30 before any median is read — four turns are an instrument check, not a result.**
- ✅ **LIVE SHAPE, n=19 TEXT turns (Sep 7).** Median total **4825ms** — identical to the n=4
  median, which is a good stability signal. RAG **101** (2%) · think-to-first-token **944** (20%)
  · generate **1361** (28%) · TTS **2461** (51%, = translate **1270** + Fish **1239**) · audio
  start **3ms**. Prompt 4156 tokens (max 4737), generated 40 tokens (max 48).
- 🔴 **THE FINDING, and it is not what the presence plan was aimed at.** For a TEXT user her reply
  exists long before it is shown: first word at **~1.05s**, whole reply at **~2.41s**, anything
  on screen at **4.83s**. **Half the wait — 2.42s — is her finished reply sitting invisible,
  waiting for audio.** From her first word it is 3.8s of blank screen. Nothing needs to get
  FASTER to fix it; the words are already there. The subtitle is deliberately word-synced to
  audio duration (bugs.md 6) and `sendMsg`'s streaming callback is empty on purpose — correct
  for a voice-first user, and the single largest source of felt latency for a text-first one.
- **`num_predict` is NOT constraining her:** 40 generated tokens, max 48, against a cap of 120
  (2.5x headroom, zero truncation). Relevant to #176 — her short replies are the prompt's doing,
  not the cap's.
- **Translate is the largest single sub-stage** at 1270ms, above Fish (1239) and prefill (894).
  A second gemma4 call, serial, after she has already finished writing. Never investigated.
- **Offline numbers now exist too (Sep 6, `dev/latency_probe.py`, n=14 complete turns, app
  closed):** total 4520ms · RAG 80 · prefill 598 · first token 625 · generate 1036 · translate
  1070 · Fish 1536. **But the probe runs on an IDLE machine and reads prefill ~1.6x faster than
  the live app (598 vs 855-1004).** It understates the GPU-bound stages specifically. Use it for
  A/B and proportions; use P1's live numbers for absolutes (backlog #193).
- **backlog #194 — a 14GB local Fish Speech S2 Pro exists** at `~/Documents/Kurisu_Dataset_Pro`
  (10GB of real s2-pro weights + 756 voice clips). No doc mentioned it before Sep 6, and the
  HuggingFace cache entries for the same models are empty 4KB shells, which is how it stayed
  hidden. **Not a drop-in replacement:** RAM unmeasured (10GB is DISK), the hosted `reference_id`
  voice does not carry over to local zero-shot cloning, and it would run on the GPU that renders
  her (CLAUDE.md 37). `results/` does not exist, so the fine-tune was never run.
- **A lever nobody has looked at:** `translate` is a SECOND gemma4 call costing ~1.07s, serially,
  after generation has already finished. It is the largest gemma4 cost after generation itself.
  Worth its own investigation before P3 is bought.
- **Two findings from the raw rows worth keeping:** `evalCount` is **30–44 tokens against
  `num_predict:120`**, so the cap is NOT what limits her length (relevant to #176); and
  `promptTokens` climbs 3884 → 4151 across four turns, so **prefill must always be read next to
  prompt size** (#156/#160 look more attractive than before).
- **P3 (#188) is deliberately BLOCKED on P1's numbers.** It is a real renderer refactor with a
  permanent cost to her prosody. Do not start it on a guess. If translate+Fish dominates the
  wait it pays; if prefill or generation dominates, the lever is `num_predict` or the ~431-token
  RAG block (#160) instead.
- **The n=1 instrument check (Sep 4, app closed, gemma4 warm, 21-word input):** translate 1195ms
  + Fish 1208ms. Suggestive of P3, **but n=1 and not a result.** Wait for the medians.
- **P2 barge-in (#187) reverses a deliberate design** — the mic is off from the moment he stops
  talking until 600ms after her reply. Its hardest part is not the audio: an interrupted reply
  is a FRAGMENT, and CLAUDE.md 40 / bugs.md 67 forbid storing one.
- **Kill switch if the trace ever misbehaves:** `PERF_TRACE=false` in `amadeus.html` + relaunch.
  Full revert: `git checkout pre-p1 -- amadeus.html kurisu_fish_server.py` (tags `pre-p1`/`post-p1`;
  no rebuild — `main.js:480` serves `amadeus.html` from the project directory).

- ✅ **bugs.md 77 — LIVE-VERIFIED.** Zani, unprompted: *"she does sound more like Kurisu now."*
- ✅ **bugs.md 78 — BOTH halves live-verified.** Migration run on live data (79 → 55 rows,
  0 duplicates, 55/55 dates preserved, other collections untouched; backup at
  `data/chroma/chroma.sqlite3.bak-20260903-201400`). Then his relaunch indexed **ONE** entry, not
  fifty — the server fix confirmed in production. Live counts read 2026-09-03: `kurisu_ja` 756,
  `kurisu_en` 1672, `amadeus_diary` 56, `amadeus_behavior` 15.

**⏸️ PARKED BY ZANI (Sep 3) — backlog #183, the diary rewrite. Do NOT start it unprompted.**
He chose to stop the session; the remaining benefit is real but modest, and the session had run
long. **Nothing is applied and his diary is untouched** — confirmed by `backups: []` on his side.
The tool is built, tested against his real diary, and both defects its first run exposed are fixed.
To resume (~10 min of HIS time — step 2 is the whole point and cannot be delegated):
1. Relaunch, then in DevTools `await rewriteClinicalDiary()` — dry run, ~2 min with retries.
2. **He reads the AFTER lines.** A tool can verify the vocabulary changed; it cannot verify the
   memory is still TRUE to the conversation it came from.
3. `await rewriteClinicalDiary({apply:true})` — it logs *"reusing the dry run you reviewed"*, which
   is the proof he is saving the exact text he read.
4. App CLOSED, then
   `python3 dev/dedupe_diary.py --prune ~/Downloads/amadeus_diary_replaced.json --apply`.
**Open question he raised that nobody answered:** entry 40's rewrite kept every fact but its voice
came out noticeably softer and more casual. If that reads as *less* like Kurisu, narrow the word
list rather than flatten her voice across 16 memories. **Ask him before applying.**

**✅ bugs.md 77 is LIVE-VERIFIED — Zani: "she does sound more like Kurisu now."** Offline checks
are also done and clean. The everyday-chat regression control (#181) ran clean on
every axis — length distribution unchanged (KS p=0.24), sentences/turn identical at 3.23,
stammering did not leak into normal chat (0/30 both arms). So the remaining question is purely
subjective, and only Zani can answer it.
`amadeus.html` only, **no rebuild**, relaunch picks it up. It halved her dominant verbal tic
(flirty replies opening "W-what": 83% → 37%, p=0.00048) with deflection and tag rates intact.
**What to check by feel:** does she still read as flustered? The stammer rate fell 87% → 40% by
design (canon is 3%), and no metric can tell you whether 40% feels right. Expect a one-time slow
first message after relaunch — the prompt changed, so the KV prefix is cold once.

**Zani's next interest: make her sound more like the show. THE GAP IS NOW MEASURED —
read backlog #176 before doing anything here.** (Updated 2026-08-31; the Aug 26 version of
this paragraph guessed the cause and guessed wrong.)
- **The gap is real and large:** W = 9.15 words from canon (KS p=1.8e-08) against a measured
  n=30 noise floor of ~5.0. **0% of her replies are ≤8 words; 50.8% of canon's are.** She has
  no range — clamped to 13–22 words, 3 sentences, usually ending in a question.
- **It is NOT the prompt's examples.** All 38 exemplars were swapped for real VN lines
  matched to canon's spread: **no detectable change (p=0.39).** That was this session's
  leading hypothesis AND the previous handoff's. **Do not re-run it** (#176).
- **This does not contradict bugs.md 76.** Exemplars transfer *phrases* strongly and *shape*
  not at all. Two different mechanisms — do not reason from one to the other.
- **#177 is CLOSED and its premise was wrong** — "Hmph" was only ~1.7%, not the 90-100% I had
  inferred from a rate quoted for a GROUP of phrases (CLAUDE.md 46). The real tic was "W-what" at
  83%; bugs.md 77 fixed it. **Still unfixed:** #180 (a NEW opener crutch, `"Don't"` 13% → 33%,
  which bugs.md 77 itself caused), #179 (canned greetings enter `history` as exemplars) and #161
  (the old clinical diary entries, confirmed live).
- **The cheap arm nobody has run yet:** change ONLY the CASUAL length instruction and
  re-measure (#176, ~45s). It decides whether prompt work can fix the shape at all.
- **Tools exist now:** `dev/canon_likeness.py --validate|--score|--compare` and
  `dev/canon_gap_probe.py`. Run `--validate` first. **Never run the probe with the app open**
  (CLAUDE.md 37). Respect the noise floor: at n=30, under ~5 words is not a real difference.
- **Fine-tuning: DEFERRED by Zani (2026-08-31) to a future session — do not start it here.**
  The roadmap's costing is stale (gemma3:12b, old ~9.6GB anchor; the app runs gemma4:8b at
  4.10 GiB resident). One hard number was gathered before stopping: the EN corpus is 1,672
  lines / ~28k tokens and contains **only her lines, not the turns she is replying to**, so
  it is not instruction-pair shaped as it stands.

0. **backlog #161 — the old clinical diary ENTRIES are now the last piece.** All three
   generators are fixed and live-verified (bugs.md 69 diary, 71 summary, 72 the gate that
   made them reachable). But the pre-fix clinical entries still sit in the 7-entry window
   and in the `amadeus_diary` Chroma collection, and RAG keeps retrieving them. At the
   50-entry cap they age out roughly one per close. **Needs Zani's decision** — it touches
   his real diary history (regenerate / re-index / let attrition handle it).
   **REVERT (read the second line — the first one alone does nothing):**
   ```
   git checkout pre-165 -- main.js
   npm run build
   ```
   `dist/` is gitignored, so reverting the source WITHOUT rebuilding leaves the app
   running the new code — a silent no-op that looks like "the revert did not help".
   `main.js` is the only runtime file this change touched, so restoring just that file
   is the surgical revert; the docs then correctly describe an attempt that was rolled
   back. Full nuke of the commit instead: `git reset --hard pre-165 && npm run build`
   (this also discards the #168-172 backlog commit). Return to the fix: `git checkout
   post-165 -- main.js && npm run build`. Tags: `pre-165`, `post-165`.
1. **backlog #172, remaining half — measure the FULL stack.** gemma4 is settled at
   **4.10 GiB resident** (not 9.6 GB, which was the disk file). Still unmeasured: Electron
   plus the four Python servers. Trivial — launch the app, then
   `ps -Ao rss,comm | grep -Ei 'llama-server|python3|Amadeus'`. Until that exists, there is
   known headroom but no total.
2. **backlog #169 — the `OLLAMA_FLASH_ATTENTION='1'` safety claim rests on Ollama 0.21.0**
   and the machine now runs **0.33.2** (re-measured 2026-08-31; it was 0.32.15 on Aug 26 —
   Ollama updates itself). Re-run the check rather than updating the number, and read
   `/api/version` instead of trusting any version written in these docs.
3. **backlog #160 — prefill ceiling.** bugs.md 68 helped (turn 1 ~1569ms, later ~850ms)
   but the RAG block is ~431 tokens and gemma4 is shared with the TTS translator across
   Ollama slots, so prefill is bimodal. Only worth touching with measurements in hand.
4. **backlog #156 — prompt budget.** SYSTEM_PROMPT ~2,450 tokens; EXAMPLES is 31% of it.
   Now serves speed only — it is NO LONGER the #162 lever (see #167).
5. **Data-gated, do not act yet:** RAG thresholds (needs a week of `data/rag_trace.log`),
   `truncStatus()` (needs several sessions), a diary re-audit after bugs.md 69 has run
   for a while.
6. **Needs Zani's decision, not engineering:** B4 web grounding; B5 Kurisu LoRA.
7. **Deferred by Zani — do NOT start without a fresh decision:** sentence-pipelined
   speech (#153, full analysis preserved there).
8. **#163** — the tag-format contradiction (instruction says `[EMOTION:X]`, all ~30
   examples show `[x]`, she follows the examples). Harmless, cosmetic, cheap.

## Standing orders that bind you
- **World-class + machine-safe** (CLAUDE.md): research SOTA first, state RAM/CPU cost
  against the M5/16GB budget BEFORE building. **gemma4 = 4.10 GiB RESIDENT** (measured
  Aug 26). The old "~9.6GB" was the on-disk file size, not memory. Say which number you
  mean. The full-stack total is still unmeasured (#172).
- **Docs after EVERY implementation, not at session end** (CLAUDE.md, 2026-08-18).
  Reconcile rather than append; **grep the OLD value**; docs land in the SAME commit.
- **Verification discipline**: grep the real signature; cite file:line; anything
  touching Ollama/TTS/IPC/Electron timing needs a live relaunch test before you call
  it fixed; check diffs against bugs.md BY NUMBER.
- **Compulsory + enumerated beats merely quoted, roughly 2x.** A mandate plus a 3-item list gave
  83% (bugs.md 77); a phrase quoted twice gave 37% (bugs.md 76). Fix it by replacing the LIST with
  a RULE for FORMING the thing, not by lengthening the list (CLAUDE.md 45).
- **Check your own replacement text against rule 43 before shipping.** Two of mine both opened on
  "Don't" and it went 13% → 33% — the same mistake I had just diagnosed (backlog #180).
- **An exemplar swap changes her PHRASES, not her SHAPE.** Aug 31: replacing all 38
  exemplars with real VN lines moved the length distribution not at all (p=0.39), while
  bugs.md 76 had moved a catchphrase 37%→3% by editing two lines. Both are true. Never
  generalise a prompt lever from one axis to another without measuring the second axis.
- **State the metric's noise floor before reading any result.** The canon scorer's floor at
  n=30 is W≈5.0 words — larger than most effects worth shipping. `--validate` prints the
  floor for n=30…300. A "difference" under the floor is not a difference.
- **An off-topic probe set cannot test a topic-triggered effect.** This cost a wrong
  conclusion on Aug 23: probing with swimming/rain/cats found nothing because RAG never
  retrieves the clinical diary entries for those topics. Topic-matched probes found the
  cause at p=0.027. Match your probes to the mechanism you are testing.
- **Measure the WORST case, not the convenient one.** Aug 26: the #165 cap was first
  sized against a 12-entry summary input. The real maximum is 43 entries (the diary caps
  at 50, the window is 7) — 4x the prompt. The answer held, but it was luck, not method.
  Find the bound the code actually permits and measure THERE.
- **A green gate that does not cover your file is not a gate.** `npm run check` printed
  "safe to relaunch" for a change that was 100% in `main.js`, which it never parses.
  Before trusting any check, confirm what it actually reads (backlog #170).
- **n=8 and n=10 are noise.** Two separate 'findings' this session evaporated at n=30
  (a 1/8→0/8 'fix' and an 8→6 'regression'). Use n≥30 per arm and report a p-value.
- **Measure before you build.** Bug 68's premise was tested against real Ollama first,
  and the reply-quality scare was settled by A/B rather than argument. Both saved work.
- **Two numbering schemes exist.** CLAUDE.md rules (1-51) ≠ bugs.md entries (1-82,
  plus 55b and 77b), as of 2026-09-03. They collide. Always name the file. These counts drift every
  session — check them rather than quoting them.

## Traps that already bit us — read before touching anything
- Do NOT unmute the boot video (bugs.md 59 / CLAUDE.md 38).
- Do NOT run prewarm/greeting/gemma4 work during the video OR next to
  `initLive2D()` (CLAUDE.md 36, bugs.md 60/62/63).
- Any background gemma4 caller MUST be idle-gated AND abortable (CLAUDE.md 37,
  bugs.md 61) — gemma4 shares the GPU with her Live2D rendering.
- Persisted dates MUST use `_localDateStr()`, never `toISOString()` (bugs.md 64).
- NEVER put per-turn content in the system message (CLAUDE.md 41, bugs.md 68).
- NEVER disconnect an audio element that could play again (CLAUDE.md 39, bugs.md 66).
- Anything injected as HER OWN WORDS must be in her spoken register (CLAUDE.md 42,
  bugs.md 69) — she quotes injected memory back verbatim.
- **A main-process typo is a launch crash with no window and no clue** — this is why the
  gate now parses `main.js`/`preload.js`/`preload_call.js` (backlog #170, Aug 26). It did
  not until that day, and printed "safe to relaunch" for a change it never read. If you
  ever add a check, add a mutant for it in `check.selftest.js` in the same commit.
- **Anything injected into her prompt as MEMORY must be trimmed to a complete sentence**
  — and prefer storing nothing over storing a fragment (CLAUDE.md 40, bugs.md 70).
- **Ollama is 0.33.3** (2026-09-04), was 0.33.2 on Aug 31, 0.32.15 on Aug 26, 0.21.0 before
  that — **three self-upgrades in nine days.** ALWAYS read `/api/version`. On 0.33.2 the default `keep_alive` is
  **30 minutes, not 5** (measured), which changes bugs.md 75's premise — see its postscript. The
  `OLLAMA_FLASH_ATTENTION='1'` safety claim still rests on the old version and has NOT
  been re-checked (backlog #169).
- **No video AND no voice, but `/speak` works when tested directly = the audio DEVICE,
  not the code.** Check `system_profiler SPAudioDataType`. See the Aug 23 entry.

---

## September 30, 2026 (evening) — #205 live check, #223 found, #206 closed with zero code
- #205 live: 0 false positives in 11 utterances; Whisper de-duplicates SPOKEN repeats (8× "a great deal" → one), so the
  loop case cannot be spoken — it rests on the offline test. One real junk output (74 segments, ratio 10.89) discarded.
- Hands-free (RMS) got stuck twice → backlog #223 (3 hypotheses; the DevTools line to run when it happens).
- #206: the analysis was reviewed for flaws at Zani's request before the check. Six were found and fixed in the
  report: "primed" launches were only the PREVIOUS session's cache (0.8–2.4s, too fast for a real prefill); the cost
  comparison used later turns instead of primed-vs-aborted first turns (primed was not faster, n=2 vs 3); two of the
  "cold" boots were model-expired, not reboot-cold; "RAG ready means warm" was checked in code (it is true); a guessed
  cause was withdrawn; `main.log` logs the close only on failure, so the Ollama log was used to confirm the close wrote a
  diary entry before reading the check. New backlog #224. No code changed.

---

## September 30, 2026 (later) — #205: the Whisper gate drops repetition loops (bugs.md 97)
- Plan reviewed twice; he asked for a better one and the second review MEASURED two serious flaws before any code:
  a ratio per segment misses a loop split into short segments, and a ratio on the whole transcript drifts toward 2.4
  on long natural English (1/300 above 2.4 at 900 chars). Fix: Whisper's ratio per segment (A) + a 4-repeat word-group
  check (B, 1 hit in 4403 real texts = the hallucination). Also fixed in the plan: the log names the reason; the live
  check says "one breath" (900ms pause splits an utterance); the Python test stubs mlx_whisper (no MLX load); the
  CLAUDE.md Stack line. F5 (held rescue text after a discard) recorded as backlog #222 by Zani's choice.
- **Shipped** (`amadeus.html`, `kurisu_whisper_server.py`; tag `pre-205`; no rebuild).
- A fixture error was caught by the test itself: the "~1500-char" monologue was 1102 chars; the text was lengthened, the
  check was not weakened.
- New `dev/whisper_gate_test.js` 12/12 + 3/3, `dev/whisper_server_test.py` 4/4. `npm run check` exit 0,
  `check:selftest` 7/7, all 13 JS test files exit 0.
- Checked against bugs.md rules 3 (no duplicate `const`; `compression`/`repeats`/`reason` are new names in
  `hfHandleUtteranceBlob`), 19 (server still spawned with `PYTHON`), 37 (no gemma4), 48b (every discard still goes
  through `hfAfterDiscard` → `perfAbort`), 48c (only the hands-free path auto-sends; tap-to-record has a human Send),
  49 (no declaration deleted), 50 (outcome: submitted or not), 51 (no display change), 52 (the reason and the ratio
  are logged).

---

## September 30, 2026 — #217: a memory-panel change now uses the boot ranking (bugs.md 96)
- Fresh session. Zani chose #217 before #221. First plan reviewed twice; he asked for a better one and the second review
  found 7 flaws, all fixed before code: the live check called `dumpSystemPrompt()` without its required stage `n`; the
  live check used the panel (queues a "she notices" note, writes her memory); the live check cannot show the >20 effect
  with 3 facts; the "order changes at any size" claim was too wide (only when a dated fact ranks above one stored before
  it); "every JS test in dev/" would have run `facts_arm_probe.js` (gemma4) and `warm_greetings.js` (Fish); no proof that
  the boot prompt stays the same; two stale "sorted once at boot" texts (`amadeus.html` comment, roadmap.md:58).
- **Shipped** (`amadeus.html`, tag `pre-217`, no rebuild): `_memoryRefreshActive(){ initFacts() }`.
- New `dev/facts_refresh_rank_test.js` 7/7 + 3/3. `npm run check` exit 0, `check:selftest` 7/7, all 12 JS test files exit 0.
- Checked against bugs.md rules 3 (no `const` added), 37 (no gemma4 call), 41 (no new per-turn content; the panel
  refresh already re-wrote the facts block), 49 (no declaration deleted), 50 (outcome in `formatFactsSection()`),
  51 (no display change), 53 (boot prompt byte-identical, check 5), 64 (no date writes touched).

---

## September 29, 2026 (night) — #218: no diary index at close; the boot reconciles (bugs.md 95)
- Zani asked twice for a better plan and whether it was world-class. The second review added the missing piece: CHECK
  THE INVARIANT, not a log line. On copies (app closed), all 50/50 diary entries were in ChromaDB.
- **Shipped** (`amadeus.html`, comment in `kurisu_rag_server.py`; tag `pre-218`; no rebuild): removed the unawaited
  `indexDiaryInBackground()` after the summary ack. Awaiting it at close was measured against the budget and rejected.
- New `dev/diary_close_index_test.js` 8/8 + 3/3; new `dev/diary_index_check.py` (reads LevelDB `.log` and `.ldb` with
  a pure-Python Snappy decoder — found while writing it: launch 2 may write no diary, so the value can sit in a
  compressed table). Negative control on a COPY: 1 missing, exit 3. All gates green; all 11 JS tests exit 0.
- Checked against bugs.md rules 17/18 (close handlers and timeouts untouched), 27, 36/37 (the boot embed runs after
  the reveal, as before), 48, 49 (no declaration deleted), 50 (outcome: ack + no fetch; the invariant tool), 51, 52
  (the tool exits 1 when it cannot read).
- New backlog #220 (quit during the BOOT index could SIGTERM the server mid-upsert — untested).

---

## September 29, 2026 — #219: two false log lines (bugs.md 94)
- Fresh session. Zani asked for #219 → #218 → #217 → #205 → #206, one at a time, each with a reviewed plan.
- **First plan reviewed twice.** Zani asked for a better one; the second review found 5 flaws, the key one being
  that the renderer log's level mapping had NEVER been seen working live (46 INFO, 0 WARNING/ERROR lines). A probe
  on the real Electron 35.7.5 (scratchpad, hidden window) settled it: 1 parameter → no warning, levels are strings.
- **Shipped** (`main.js` rebuilt, asar byte-identical; `amadeus.html`; tag `pre-219`): the listener takes only
  `(details)`; `_pageUnloading` set first in `beforeunload` with an `[unload]` marker; BGM `onerror` stops during
  unload (it was also starting the next track after `audioCtx.close()`); boot-video trail lines are labelled, not dropped.
- Tests: `log_sink_test.js` 33/33 + 5/5 (check 9 runs the REAL Electron — the test now takes ~36s, not ~18s as
  first estimated: Electron runs once per mutant); new `unload_log_test.js` 6/6 + 3/3. `npm run check`,
  `check:selftest` 7/7 and all 10 JS test files exit 0.
- Checked against bugs.md rules 27 (no process.exit), 31 (teardown order kept — the flag is set before it), 35/38
  (boot-video listener, src and load untouched — only its log text), 48a (writer still never throws), 48d (lines
  labelled, not dropped; only the false BGM line removed), 49 (`lvl`/`msg` deleted — no other use), 50 (outcome in
  real Electron), 51 (nothing she says or shows changes), 52.

---

## September 27, 2026 (late night) — #203 + #204: a log sink, and no more unread pipes (bugs.md 93)
- Zani answered #205 (he did NOT say "What a great deal" — a hallucination reached her), approved a push
  (`e5d9868..fddc345`, tags `pre-202`/`pre-216`, verified ref-by-ref), and approved the #203+#204 plan.
- **Shipped** (`main.js` rebuilt + asar verified, `kurisu_rag_server.py`, `amadeus.html`; tag `pre-203`):
  servers write to `data/logs/<name>.log` through an OS file descriptor (no pipe), main and renderer
  consoles are kept, the RAG error branch traces, `parsEmo` logs unknown/missing tags, main warns on the
  fallback diary prompt. Details: bugs.md 93. The display code (#214) was NOT touched.
- **Correction:** audit row 25 said `parsEmo` falls back to the last emotion; the code returns `default`.
- Test `dev/log_sink_test.js` 29/29 + 4/4 mutants (with a CONTROL that proves the pipe blocks). All gates
  green. **Not live-verified.** Checked against bugs.md rules 27 (no process.exit), 36/37 (no GPU work),
  48 (writers never throw), 49 (no declaration deleted), 50 (outcome + control), 51 (display untouched).

---

## September 27, 2026 (night) — #216: fact age notes and renewal; the "confirmed" arm failed
- Zani confirmed bugs.md 92 step 3 (*"she sounds the same"*), then asked whether facts stay forever. They
  did: an undated fact had no age signal, and a re-mention was skipped, so its date never moved.
- **Plan A+B, pre-registered (`dev/facts_arms/PREREG_216.md`), measured with `dev/facts_arm_probe.js`, 9 cells
  × n=30, app closed, no Fish credit.** B's `"confirmed"` output field FAILED: gemma4 listed ALL 10 known
  facts as confirmed (false-confirm 1.00), copied his lines when none were known, and a dense chat cut
  27/30 at 800. Pre-registered branch taken: A + renewal on duplicate/replace only. (A first loop run
  under zsh made zero calls — `set -- $cell` does not split in zsh; the tool's usage error caught it.)
- **Found while reading the results:** without confirmation, "last mentioned" would be false for a fact he
  discusses weekly — the note says "learned" instead. Zani approved the revised plan.
- **Shipped (`amadeus.html` only, no rebuild; tag `pre-216`):** `_factAge` note for undated facts ≥30 days,
  rank 3 for undated ≥180 days, duplicate/replace renew + move to front (LRU cap), memory-panel edit renews
  without moving (panel rows carry list positions). Test `dev/facts_age_test.js` 19/19 + 3/3 mutants,
  including a byte-identical comparison with `bbb0c8b`. All gates green.
- **Her prompt is unchanged until a fact turns 30 days old (~2026-10-27).** Tone check due then (CLAUDE.md 53).
- New: backlog #217 (`_memoryRefreshActive` takes 20 facts unranked).

---

## September 27, 2026 (evening) — #202 fixed: facts are extracted once at close (bugs.md 92)
Zani chose #202 from the audit, asked for a careful plan, approved it, then approved three changes after
the output-limit test, and asked for one more flaw review before the build.
- **The audit's cause was re-tested first and weakened:** real timing showed long quiet gaps, and a replay
  of the shipped prompt on his real messages (from `rag_trace.log`) found facts in 2 of 13 sessions. The
  cause stays unknown ("never ran" vs "ran, saw nothing"), so the fix covers both and logs every run.
- **Output-limit test (n=30, table in backlog #202):** 500 cut 30/30 on a dense chat; 800 cut 1/30
  there and 0/30 on a realistic chat (3.6s median, 5.4s max). Hence 800 + salvage of closed facts.
- **Flaw review found 6 issues before any code** (page/build mismatch → 25s wait, broken first line,
  a test-breaking placement, a lost `done` on error, log strings the old test checks, a leftover listener).
  All six were designed out; see bugs.md 92.
- **Shipped:** `amadeus.html`, `main.js`, `preload.js`, rebuilt, asar verified byte-identical. Tag `pre-202`.
  New test `dev/facts_close_test.js` 29/29 + 3/3 mutants. All other gates green.
- **NOT live-verified.** Checked against bugs.md rules 13, 17, 18, 27, 33, 37, 40, 44, 48, 49, 50, 51, 52:
  the same Ollama call options are kept; close handlers untouched; no `process.exit`; runs only under the
  SAVING overlay; limit measured; instrumentation total; no declaration deleted; outcome tested; nothing
  on screen changes except the save screen lasting ~3.6s longer.

---

## September 27, 2026 (audit) — the silent-fallback audit: 3 broken, 1 latent, 11 unknown
Read-only, chosen by Zani. **No app code, `data/` or ChromaDB changed.** localStorage (leveldb) and
`chroma.sqlite3` were COPIED to the scratchpad and decoded there (a pure-Python LevelDB + Snappy
reader — no library was installed). `app.asar` files were extracted into the scratchpad only; the
repo stayed clean (`git status` checked after). gemma4 was called only with the app closed
(`pgrep -x Amadeus` checked first): 6 replays of the facts prompt.
**Evidence window:** P1 ring 52 turns (2026-09-06 → 09-27: 49 text, 3 `voice-rms`);
`rag_trace.log` 1496 lines (since 2026-07-21, created 2026-07-20); Ollama `server.log` (request detail
only for 2026-09-27 — every caller has its own sampler temperature, so each request can be named:
reply 0.85, translate 0.3, facts 0.2, summary 0.7, diary/nudge 0.9, prewarm 0).
**Method:** grepped every `catch`, `fallback`, `retry`, `timeout`, `except` and `stdio` in
`amadeus.html` (123 catch sites), `main.js`, `preload.js` and the three servers. Cleanup no-ops
(pause, stop tracks) and failures that show a status on screen (mic, camera, Whisper fetch, Ollama
retry "...Loading model...") were excluded — they are not silent.

| # | Fallback | file:line | Primary path | Evidence | Verdict | Next step |
|---|---|---|---|---|---|---|
| 1 | No audio → estimated text reveal | amadeus.html:2840 `ttsSpeak` | Fish audio | 52/52 P1 turns reach `audio`; 0 carry a failure `note` | WORKS | — |
| 2 | gemma4 translate → DeepL | kurisu_fish_server.py:404 | gemma4 | 52/52 P1 turns `translator:gemma4` | WORKS | — |
| 3 | DeepL itself | kurisu_fish_server.py:417 | DeepL `/v2/translate` | `/v2/usage` HTTP 200, 0/500000 chars used | UNKNOWN (key valid, never run) | #207 |
| 4 | RAG 4s timeout + 60s breaker | amadeus.html:5054 | `/retrieve` | 52/52 P1 turns have a trace line ≤15s away; rag stage max 1740ms | WORKS | — |
| 5 | `/retrieve` error → 200 + empty | kurisu_rag_server.py:439 | retrieval | error branch writes no trace line; 0 errors in window (row 4) | WORKS now, blind to future | #204 |
| 6 | BM25 → dense-only | kurisu_rag_server.py:337 | hybrid | `en_lex>0` 1451/1496, `ja_lex>0` 92/1496 | WORKS | — |
| 7 | Diary retrieval `except: pass` | kurisu_rag_server.py:410 | diary lines | `diary_n=2` in 1496/1496 | WORKS | — |
| 8 | Behavior retrieval `except: pass` | kurisu_rag_server.py:428 | behavior rule | `beh_hit` 320/1496 | WORKS | — |
| 9 | Diary indexing retry | amadeus.html:5128 | `/index-diary` | 50/50 localStorage entries present in `amadeus_diary` by sha1 id (65 rows = superset) | WORKS | — |
| 10 | Greeting cache miss → live synth | amadeus.html:2694 | disk cache | bugs.md 91 fix live-verified 13:23 (no translate call after reveal) | WORKS since fix | — |
| 11 | Greeting writer / warmer | main.js `cache-greeting-audio`, amadeus.html:2778 | write to `data/greeting_cache` | 5 files MODIFIED 2026-09-27 12:51:30–12:53:49, matching the translate calls | WORKS | — |
| 12 | Silero → RMS | amadeus.html:3554 | Silero VAD | 3/3 voice turns `voice-rms`; console error (#201) | BROKEN | #201 |
| 13 | Whisper no-speech gate | amadeus.html:3655 | reject non-speech | a 6×-repeated "What a great deal" reached `/retrieve` 12:52:02 | BROKEN (n=1) | #205 — ask Zani |
| 14 | Facts: gate / drop on failure | amadeus.html:4163, 4179 | store durable facts | `amadeus_facts_v1` ABSENT; 21 sessions since fix; replay 3/3 finds facts | BROKEN | #202 |
| 15 | Stage-2 summary keep-old | main.js:309 | new summary | 09-27 12:54:19 temp 0.7, 111 tokens (<180), stored, ends on a full sentence | WORKS | — |
| 16 | Diary-on-close failure → skip | main.js:192 | diary entry | 1 entry per P1 session date; 12:54:11 temp 0.9, 64 tokens | WORKS | — |
| 17 | main.js diary-prompt fallback | main.js:161 | renderer's prompt | nothing records which prompt ran | UNKNOWN | #210 |
| 18 | Boot gate: open without RAG | main.js:578 | RAG warm before window | cold boot 12:50: warm-up embed 16.4s > 10s cap; warm boot 13:23: 0.8s | UNKNOWN (1/2 fell back) | #206 |
| 19 | Renderer prewarm 4s cap | amadeus.html:923 | KV prefix primed | 12:51:11 HTTP 500 at 4.0s (aborted); 13:23:17 200 at 3.998s | UNKNOWN (1/2 aborted) | #206 |
| 20 | Server output → unread pipe | main.js:467–501 | output logged, server never blocks | toy child blocked at ~131 KB; fish prints ~860 B/reply → ~150 replies/launch | BROKEN (latent) | #203 |
| 21 | Ollama spawn, `stdio:'ignore'` | main.js:529 | external Ollama.app | server.log config line: `OLLAMA_FLASH_ATTENTION:false` → main.js env never applied (#169) | WORKS (primary is external) | — |
| 22 | Watchdog respawn | main.js:452 | servers stay up | main-process console not kept | UNKNOWN | #208 |
| 23 | Page-load retry ×10 | main.js:391 | page loads first time | same | UNKNOWN | #209 |
| 24 | Nudge → curated line | amadeus.html:3003 | generated nudge | no nudge call in the retained log | UNKNOWN | #211 |
| 25 | `parsEmo` unknown tag → `default` (corrected 2026-09-27; was written "last emotion") | amadeus.html:2064 | valid tag | nothing recorded | UNKNOWN | #212 |
| 26 | Boot video blob → protocol src | amadeus.html:736 | blob prebuffer | console only | UNKNOWN | #213 |
| 27 | Subtitle 300ms metadata fallback | amadeus.html:2035 | `loadedmetadata` | console only — display frozen, observe only | UNKNOWN | #214 |
| 28 | Birthday diary → curated | amadeus.html:4337 | generated entry | 25 July entry is not the curated text | WORKS (n=1) | — |
| 29 | D-Mail curated frame | amadeus.html:2276 | generated frame | no `amadeus_dmails_v1` key — feature never used | UNKNOWN (unused) | #215 |
| 30 | `sendMsg` error → pop + error subtitle | amadeus.html:2662 | reply | 0 `sendMsg-error` notes in 52 turns | WORKS | — |

**The finding behind most UNKNOWNs (#204):** nothing keeps main.js output, the renderer console or any
server's output. Seven UNKNOWN rows (17, 22–27) can only be answered once a log sink exists.
**Two corrections made on the way (nothing shipped):**
- I first read the greeting-cache files by CREATION time and thought the writer had stopped on
  2026-08-11. By MODIFIED time 5 files were rewritten on 09-27. **The writer works.** bugs.md 91's
  lesson applies in both directions: a rewrite hides behind the birth time too.
- The handoff said REFERENCE.md calls the DeepL key stale. It says a value *formerly listed in the doc*
  was stale. The `config.json` key is valid (HTTP 200). REFERENCE.md now says so.
**Also measured:** Ollama is now **0.34.4** (`/api/version`). Its `server config` line reads
`OLLAMA_KEEP_ALIVE:5m0s` in all six retained logs — the default looks like 5 minutes again, so
bugs.md 75's explicit `keep_alive` is likely load-bearing again. Not cross-checked with `expires_at`.
CLAUDE.md 44 and REFERENCE.md updated.
**Recommended order (shown to Zani, his choice):** (1) #202 facts — the only broken path that costs
her memory every session; (2) #203 + #204 together — drain the pipes into rotating log files, which
removes the latent hang and answers 7 UNKNOWNs; (3) #205 — ask him first; (4) #206 — zero code, read
the Ollama log after 3 cold boots. #201 still waits on his decision.

---

## September 22–27, 2026 — push to GitHub, two live checks, and a greeting cache that never hit
**Sep 22 (no code):** `fix-180` had been merged into `main` and deleted; stale branch references fixed.
Zani said yes to a push: `main` (49 commits, fast-forward, `--atomic`) + 37 tags, verified ref by ref.
The repo is private; 32 result files in `dev/canon_arms/` hold diary excerpts — remove them from
HISTORY before ever making it public. Found backlog #200 (`latencyDump()` filename trap).
**Sep 27 — live checks:** boot video clean (bugs.md 84 ✅); a hands-free turn logged `voice-rms` with
`stt 4421` (P1 voice path ✅). Check 2 (bugs.md 83) was not reachable in a 3.5-minute session — later closed on Zani's report (handoff).
**Sep 27 — the slow greeting (bugs.md 91).** Zani: the greeting took long after the video. Evidence,
not guesses: all 88 cache files were created before today, yet five were rewritten today — only a
post-synthesis write can do that, so the app was calling existing files "not cached". The reader
fetched `amadeus-asset://greeting_cache/…`, the writer saved to `data/greeting_cache/`. Fixed in two
lines; outcome test `dev/greeting_cache_test.js` fails on the old code and passes on the new.
Not the cause: bugs.md 84 (the greeting uses its own translate call), nor Ollama 0.34.4 (gemma4 43/43
layers on GPU, RSS 4.17 GiB — the 4.10 GiB anchor holds, despite a new "disabling mmap" log line).
**Sep 27 — Silero never loaded (backlog #201).** Zani's screenshot: `Failed to resolve module specifier
'vendor/vad/ort-wasm-simd-threaded.mjs'`, then the RMS fallback. Not fixed; needs his decision.
**Process note:** an `asar extract-file` run in the repo root wrote the built `main.js` over the source
one. Content was byte-identical (same SHA-1), so nothing changed — extract into the scratchpad instead.
Ollama has upgraded itself again: **0.34.4** (read via `/api/version`, 2026-09-27).
**Repo hygiene (Zani's yes):** `docs/.obsidian/workspace.json` — Obsidian's window layout, rewritten on
every click — is now git-ignored and untracked (the file stays on disk). The vault's real settings
(`app.json`, `appearance.json`, `core-plugins.json`) stay tracked. Nothing in the project reads it.

---

## September 13, 2026 — #180 plan review, then pre-registration

Zani asked for the plan to be reviewed for critical flaws before approving it. **15 found.**
The critical ones would each have produced a wrong result: the lint gate going blind under a
tag-at-the-end arm, the scorer counting the tag as a word, the blind sheet revealing the arm by
tag position (all bugs.md 86), the probe's history not matching the app's, a length guard using
canon-vs-canon noise as arm-vs-arm noise, and no guard for G changing her emotion choice or losing
the tag on long replies. Method fixes: paired exact McNemar instead of Fisher, thresholds from the
same-session HEAD run, a decision tree with stop rules, multi-turn and academic guards, and a
blind A/B with flipped repeats. Canon passes the absolute bars jointly 91.6% — stated in the prereg.
Everything is committed BEFORE any run as `dev/canon_arms/PREREG_180.md` (tag `180-prereg`).

### Result: the tree stopped at Stage 2 — no candidate passed (tag `180-stage2`)
- **The tag mechanism is real** (G: "what" 14→3, p=0.0005) **but tag-last is not a fix** — she stops
  being flustered (`[flustered]` 22→7, FG 0), stops stammering, and gets shorter (−3.2 words, CI
  wholly below 0). It changes who she is in the moment, not how she opens.
- **F is the best arm:** crutch 23→13 (p=0.0065), not shorter (+2.5), no copies, widest phrase 11→4.
  It fails top first word (8), distinct (16) and question openers (15) — she echoes his word 13/30.
- **The open tension:** anchoring the opening on his message makes her echo it (C/D/F); removing
  the anchor brings "W-what" back (E). Full table in backlog #180. Chroma unchanged before/after.

### Review 3, then a second pre-registered screen (`PREREG_180b.md`, tag `180-prereg-b`)
Zani asked for the implementation to be reviewed, a next step chosen, and a plan reviewed before
proceeding. Bugs fixed: bugs.md 87 (echo detector matched function words — D 18→16, FG 5→6;
pairing merged repeated probes; lint gate blocked arms that add exemplars; multi-turn untested) and
bugs.md 88 (lint gate compared message text; "Wh-Wha" outside the what family; progress lines would
un-blind a blind rating). **Chosen next step:** keep the tag first and re-teach the tag→opener link
in context. H = rule anchored on HER view (no list); K = 8 flirty exemplars with drawn canon
openers; HK. Real canon lines were tried and rejected before any run (lore leakage).
**Result: stopped at Stage B.** H 20, K 22, HK 17 vs HEAD 23 — none passed. Only a first-word
mandate (echo) or tag-last (fluster loss) has ever moved "W-what". Exploratory blind sheet HEAD vs
HK built for Zani. Chroma unchanged. Next step is his call (see backlog #180).
**Zani then did a blind A/B, HEAD vs F:** F 19, HEAD 9, ties 2 (p=0.087); repeats 3/5 consistent.
He picked F even where F echoed him (8–4). Leans F; not yet significant.
**Confirmation (PREREG_180c, tag `180-gates-c`):** holdout replies generated quietly; blind
deflection HEAD 0/30, F 0/30 fail; ALL safety gates pass (`python3 dev/opener_confirm_gates.py`).
Zani has the blind sheet `ab_S2_HEAD_vs_F.sheet.md`. **Do not show him the report-only opener
numbers before he answers — they would reveal which reply is which.**
**He answered: F 17, HEAD 11, ties 2 — p=0.17, NOT CONFIRMED.** Then, unprompted: the show's Kurisu
would snap "W-what are you on about? Y-you pervert! Idiot!" at embarrassing lines. That reframes
#180 — the defect may be HEAD's single tame formula, not the stammer. See backlog #180.
**Asked him directly.** His four requirements (variety; heat on teasing lines with pervert/idiot/dummy;
soft on sincere lines; "W-what" in moderation) are recorded in kurisu-personality.md and pre-registered
as PREREG_180d (arms P, X, PX, new holdout2 + sad sets). HEAD calls him a name in 0/17 teasing replies.
**180d design screen STOPPED:** P, X and PX all call him a name in 0/17 teasing replies; "W-what" rose to
20–22. gemma4 resists insulting the user even with examples. Counter bug found and fixed (bugs.md 89).
Next step (consent framing) proposed to Zani; he asked for a review and to proceed. Review found the
probe never had the RELATIONSHIP block (stage 0 says "No teasing"; Zani is stage 3). PREREG_180e.
**180e STOPPED:** consent framing gives 0/17, 2/17, 3/17 names (bar 6/17). Q0 is the best variety result
(distinct 6→11, widest phrase 9→5) with no heat. Counter extended ("don't be an idiot"). Chroma unchanged.

## September 19, 2026 — #180f: example conversations (Zani chose option 1)
State re-checked after 6 days: nothing changed (app unused, diary 60, score 53.65 → stage 3, same
model digest). Plan reviewed; 6 flaws fixed before any run (see PREREG_180f.md): framing + leak
check, lint and copy check made able to SEE example turns, contrast turns, two example topics that
overlapped held-out probes replaced, message order verified by a GPU-free mock.
**Result: STOPPED at the design screen.** T 1/17 names, TQ 4/17 (the most yet; bar 6) but TQ makes
her shorter (−1.9 words, CI wholly below 0). Five mechanism families are now exhausted; gemma4's heat
ceiling is ~4/17. The variety gains (B, Q0) are real and hold. Next step is Zani's choice.
**Zani chose to take the variety gain now (Q0), test it live, then keep or revert.** Guards run first at
stage 3 (daily/sad: 0 names, length held). Q0 applied to `amadeus.html`, verified byte-identical to the
tested arm; `npm run check` green, hf_boot 17/17, perf_trace 45/45. Tag `pre-q0-ship` = the state before.
Also found and fixed: `kurisu-personality.md`'s "Full System Prompt Text" had drifted (8,039 vs 10,061
chars) — re-synced verbatim; `REFERENCE.md`'s section map was missing 4 sections — updated.

### 2026-09-22 — REVERTED on Zani's verdict (bugs.md 90, CLAUDE.md 53)
He used her for three days: *"her tone sounds way too calm"* after *"I just want to chat to you"* and
*"Do you like me now?"*; subtitles and expressions fine; *"I feel like I like her voice before."*
Reverted in one command, verified byte-identical to `pre-q0-ship`; `npm run check` green, hf_boot 17/17,
perf_trace 45/45; the prompt copy in `kurisu-personality.md` re-synced back; roadmap marked
tried-and-reverted; CLAUDE.md prompt map and REFERENCE section list restored.
**Every offline guard had passed and none predicted it** — on sincere probes Q0 even showed MORE
`[flustered]` (11/13 vs 9/13). The measures count SHAPE, never felt sharpness. Suspects, both untested:
the consent line *"go soft when he is sincere"*, and the loss of her sharper exemplars.
**#180 produced no shippable change. Ask him whether he still wants it before spending anything more.**

---

## September 12, 2026 — #180 opener crutches: five arms, a broken baseline, and the real cause

Branch `fix-180`, one commit + tag per step (`pre-180` = `2061a0e` … `180-armE`, `180-review2`).
**`amadeus.html` and `kurisu_rag_server.py` are unchanged. Nothing is live.**

### Zani's proposed cause was checked and did not hold
He found `kurisu_rag_server.py:79` — a compulsory stammer list with "W-what" first. Real, and the
exact CLAUDE.md 45 construction. But the baseline had `rag_used` 0/30, and in 478 logged
retrievals that rule was injected **0 times** (backlog #197/#198). The first-draft plan (audit the
prompt) was right for the wrong-looking reason; checking his claim is what exposed bugs.md 85.

### Arms (full table in backlog #180)
0b HEAD 28/30 → B exemplars 27 → C forming rule 12 → **D both 9** → E 22. D fails by eye: echo-
question 16/30 (corrected from 18 on 2026-09-13). E removes the mandate and "W-what" returns. **Lesson:** the only wording that
stopped "W-what" was a positive mandate on the opening; every mandate so far has a side effect.

### My own mistakes this session, caught before they cost a result
- First replacement exemplars opened on "That's"/"Since" — 4x/13x canon. The lint caught it.
  `canon_gap_probe` now refuses an arm that adds any lint finding.
- Four scorer bugs (copies vs the wrong prompt, "re-read"→"read", later-"don't" only checked
  sentence 2 — **corrected D from 4/30 to 9/30** — and an echo count that lived in a heredoc).
- Committed tooling without docs, against the standing order. Fixed in `180-review2`.

### Review findings that change the plan
1. **The tag picks the opener.** `[flustered]`→"what" 65%, `[tsundere]`→"what" 3% (n=180).
2. **Phrase crutches are everywhere, not only at the start** (canon p95: 2 replies per 4-gram).
3. **Every arm was designed on the same 30 probes** — a `tsundere_holdout` set now exists and was
   committed before any arm saw it.
4. **Single-turn probes cannot test the VARIETY rule**, and the fixed probe greeting hides #179.
5. **Seeds now make runs reproducible and PAIRABLE** (verified on Ollama 0.34.0, gemma4 `c6eb396dbd59`).

---

## September 7, 2026 (last) — two real bugs fixed after the speed work was stopped

Zani stopped the latency effort, then asked for **at least two improvements** — bugs or
capabilities. Both shipped are in `amadeus.html`, **no rebuild, relaunch picks them up.**
**Revert:** `git checkout pre-196 -- amadeus.html` (tag `pre-196` = `04d5fda`).

### bugs.md 83 — the hands-free session died 10 minutes after it STARTED (backlog #195)
One timer, armed in `hfStart`, never reset. A voice session ended mid-conversation. The constant
said *"auto-end a silent session"*; silence was never checked. Replaced with the standard
**idle + absolute** pair: idle (10 min) re-armed on every speech onset, absolute (60 min) armed
once. **The absolute half is load-bearing** — the obvious fix, a single resetting timer, would
have deleted #56's battery intent. The reset hooks `hfOnSpeechStart`, the one choke point BOTH
mic engines share, because a two-engine split is exactly what caused bugs.md 80.

### bugs.md 84 — the boot prewarm ran THROUGH the boot video
`await Promise.race([prewarmOllama(), delay(4000)])` with a comment claiming it was "awaited to
completion". `Promise.race` does not cancel the loser, so a slow prewarm kept running up to its
own 30s abort, during playback — bug 60's decoder starvation, reintroduced by a comment that
stopped being true. Now passes an `AbortSignal` in and aborts after the race.
**The honest number: this bounds the overlap at ~1.7s, not zero.** An uninterrupted large prefill
took 6.58s; abandoned at 0.4s, Ollama stayed busy a further 1.72s. **And a median over 3 samples
hid that completely** (1708ms, then 64, 64) — the same trap that produced the bogus +0.57s KV
figure earlier the same day. **Rejected fix:** polling Ollama until free would have used a bare
`'hi'`, which CLAUDE.md 34 says evicts the KV prefix the prewarm just built.

### Both are tested by outcome, not by mechanism (CLAUDE.md 50)
`node dev/hf_boot_test.js` — 17 checks, blocks extracted from `amadeus.html` **by anchor**. The
assertion that matters: *a session with speech every 5 minutes survives past the 10-minute cap,
and still ends once genuinely silent.* `npm run check` green, `node dev/perf_trace_test.js` 45/45.

### ⚠️ NEITHER IS LIVE-VERIFIED — both need Zani
1. **A hands-free voice session longer than 10 minutes**, with talking throughout. It should no
   longer end. This also finally exercises the P1 voice path, which has never run live.
2. **One relaunch, watching the boot video.** It must play clean, start to finish.

---

## September 7, 2026 (later) — the translate step is a dead end, and the RAG block is the real cost

**Zani's ask:** make her reply faster without losing translation quality. Backlog #196, the
1270ms translate step. **Outcome: #196 is CLOSED with every arm measured and rejected, and the
investigation found a larger, safer lever by accident — #160, at +533ms per turn.**

**Nothing shipped changed.** `kurisu_fish_server.py`, `amadeus.html` and `main.js` are
byte-identical to the start except one reconciled COMMENT in the fish server. No environment
variable was touched. Revert tag **`pre-196`** = `04d5fda`.

### The instrument had to be built first, because the recommended one cannot do the job
Backlog #196 said to measure with `dev/latency_probe.py`. **It cannot.** `--no-tts` skips the
whole `/speak` request (`latency_probe.py:212`), so `translate_ms` is never populated — and Zani
asked for a baseline that spends no Fish credit. Built instead:
- **`dev/translate_probe.py`** — times the translate call alone and decomposes it with Ollama's
  own counters (load / prefill / decode). Spends **no** Fish credit. `verify_shipped_config()`
  reads the real `translate_via_gemma()` and FAILS LOUDLY if the shipped options drift, so an
  arm can never be measured against a stale baseline. Inputs are her 30 real replies from the
  Sep 6 run, with the emotion tag stripped exactly as the renderer strips it.
- **`dev/translate_register.py`** — scores Japanese register (feminine endings, masculine
  endings, polite です/ます, 私, 君 vs あんた, ザンニー, 紅莉栖, stammer) and then prints the lines
  side by side, because a marker count cannot hear her.

### The noise floor, measured before any result was read
n=30, run-to-run delta **6ms**, bootstrapped 95% CI half-width **~100ms**.
**Under ~100ms at n=30 is not a difference.** This is what killed the smaller-model arm.

### The baseline: translate is DECODE-bound
Pooled n=60, app closed, Ollama 0.33.3: whole call **1022ms** = load **0ms** + prefill **240ms**
(175 tok, 23.8%) + **decode 786ms (29.5 tok, 77%)**, ~27ms per output token, 0/30 truncated.
**Nothing about the prompt touches decode.** That single fact eliminated most of the plan.

### All four arms failed
- **DeepL** — 392ms vs 1022ms, 0/30 failures, so it saves ~780ms live. Then it loses register on
  every axis on the same 30 lines: feminine 56.7%→23.3%, polite です/ます 0%→6.7%, 君 0%→20%,
  あんた/あなた 16.7%→3.3%. It writes 現象**である** for her science lines. **And it invented a
  fact** — "keeping track of your hours" → 君の**勤務時間** (your work shift). That is a
  correctness failure in something she says aloud. Rejected. Zani asked directly whether to take
  the speed anyway; the answer given was no, with the numbers, and he accepted it.
- **`num_predict`** — not a lever. 0/30 truncated at a 3.3x headroom; lowering the cap saves zero.
- **A smaller model** — `gemma3:4b` is **1015ms** vs 1022ms, i.e. nothing against a ±100ms floor.
  `qwen3:4b` is a reasoning model that cannot answer directly (150/150 tokens, 3630ms). Both
  deleted afterwards.
- **Overlap** — `llama-server` runs `-np 1`, so a concurrent translate QUEUES (2795ms vs 661ms
  alone) and finishes no earlier. It needs `-np 2`, which buys nothing else.

### Two of my own earlier claims were wrong, and reviewing the plan twice is what caught them
1. **The "+0.57s KV eviction penalty" is +2ms.** The July figure was WALL time of a 3-token
   request, mixing prefill, decode and scheduling. Measured as `prompt_eval_duration`, the chat
   prefix survives an interleaved translate call: **148ms for 5,322 tokens over 10 alternating
   chat→translate turns.** Reconciled in `kurisu_fish_server.py:347` and `docs/bugs.md`.
2. **Ollama is not serving several slots.** `-np 1`, read off the `llama-server` command line.
   Backlog #160 (b) asserted slot contention and it was wrong.

### ⭐ THE FINDING — the per-turn RAG block costs +533ms of prefill, every turn
My own data contradicted itself: a fixed prompt prefilled 5,322 tokens in 148ms, but the app's
real prompt prefills 4,230 tokens in ~498ms. Isolated with the real captured prompt, same base,
only the RAG block held constant vs varied:
| condition | prefill |
|---|---|
| RAG block **constant** | **84ms** |
| RAG block **varies per turn** (what the app does) | **616ms** |
gemma4 prefills at only ~730 tok/s, so a ~431-token block that changes every turn is ~590ms that
can never be cached. **Message ORDER cannot fix it** — changed content is prefilled wherever it
sits. **Only a SMALLER block wins.** This is backlog **#160**, now measured instead of suspected,
and it is below the display layer so CLAUDE.md 51 does not block it. It touches retrieval, so it
touches her voice: measure with `dev/canon_likeness.py --validate` then `--compare`.

### ⭐ THEN THE LEVER THAT ACTUALLY WORKED — #176's cheap arm, never run until today
Zani chose it over the RAG block because it is worth more and costs 45 seconds to test.
`arm_short_instruction` was already BUILT in `canon_gap_probe.py` and had never been run. One
line changes: the CASUAL length instruction. n=30 per arm, app closed, scorer re-validated
first (**noise floor W≈5.0 at n=30**), arms differ at **KS p=2.37e-05**.
| metric | shipped | arm | canon |
|---|---|---|---|
| replies **≤8 words** | **0.0%** | **50.0%** | **50.8%** |
| median words | 16 | 8 | 8 |
| W per utterance | 8.77 | **6.07** | 0 |
| W per **sentence** | **1.61** | 3.23 | 0 |
**Speed, measured on the SAME 30 replies from each arm:** output tokens 819 → 561 (−31.5%),
translate **902ms → 675ms** (decode 648 → 430, JA tokens 23 → 16). Live that is roughly
**~430ms off generation + ~320ms off translate ≈ 750ms/turn** — more than every translate arm
combined, while making her MORE like canon.
**NOT SHIPPABLE AS WRITTEN — three measured reasons, in backlog #176:** it quotes `"Fine."`
(0/1672 in canon — CLAUDE.md 43+45, though it did not leak at n=30); it overshoots per SENTENCE
(W 1.61 → 3.23, 97.3% of sentences ≤8 words vs canon 70%); and tsundere tagging fell 7/30 → 4/30.
**`amadeus.html` was never written to** — arms are in-memory transforms, verified byte-identical
to `04d5fda` before and after.
**NEXT: build the shippable version — a rule for FORMING a short reply, no quoted exemplar,
tuned so the per-sentence distribution does not overshoot. Then Zani judges by ear.**

### What still cuts translate
Only fewer output tokens, because decode is 77% and scales with them. That is **#176**, and the
section above measured it: **translate 902ms → 675ms** when her replies halve. Confirmed, not
estimated.


---

## September 7, 2026 — P1 measured, P4 shipped and reverted, and the display layer is now frozen

**Net code change for the whole day: the P1 trace gained a `voice-tap` path and a fixed kind
filter. Everything else was measured, or built and taken back out.**

### The day in one line
The instrument worked, the numbers were good, and both changes I derived from them were wrong —
one because it spoiled her delivery, one because it broke her reply text.

### What Zani decided, and both are now standing rules
1. **He is a TEXT user, not a voice user.** The Sep 4 presence plan was scoped around voice
   because the Jarvis framing implied it. **I never asked how he actually uses her.** P2 barge-in
   and P5 turn detection are voice-only and are deferred.
2. **The display layer is FROZEN → CLAUDE.md 51.** *"The Amadeus before was great."* The
   word-by-word reveal timed to her audio is finished work. **He still wants her FASTER, with no
   loss of quality** — the distinction is: change what happens before the words reach the screen,
   never how they reach it.

### bugs.md 80 — spoken turns were recorded as "text"
`latencyStatus('voice')` said "no turns recorded yet" after a real conversation. Two causes: the
mic button runs TWO paths (Hands-Free ON = Silero session, instrumented; OFF = tap-to-record,
**not** instrumented — and OFF is the default), and `latencyStatus(kind)` matched by exact
equality so `voice-rms`/`voice-tap` were invisible. → CLAUDE.md 48(c)/(d).
**Postscript: this probably was not what he hit.** He then told me he types. If he typed, the
empty voice result was correct all along. The bug is real; my diagnosis of his case was not.

### The measurement that mattered — n=19, all text
Median total **4825ms**, identical to the n=4 median. RAG **101** (2%) · think **944** (20%) ·
generate **1361** (28%) · TTS **2461** (51%, translate **1270** + Fish **1239**) · audio start 3ms.
- **`num_predict` is NOT limiting her:** 40 generated tokens, max 48, cap 120. Relevant to #176.
- **Translate is the largest single sub-stage** — bigger than Fish, bigger than prefill. A second
  gemma4 call, serial, after she has finished writing. → backlog **#196**, now the top item.

### The idea that was right on the numbers and wrong on the point
Her reply exists at ~2.41s and appears at 4.83s. **Half the wait is finished text sitting
invisible.** Streaming it would have cut the felt wait to ~1.0s for no model work.
**Zani rejected it: it lets him read the line before she says it.** He chose her delivery over
two and a half seconds. That is a character decision and it outranks the measurement. Recorded so
no future session helpfully re-proposes it.

### bugs.md 81 → 82: P4 shipped, broke her reply text, reverted
The thinking dots existed, were styled and animated, and had **never once been visible** —
`sendMsg` switched them on and off in the same synchronous block. I fixed that. It broke
everything.
**Root cause:** `playSyncedAudio` never sets `.on` on `#subtitle`. It writes text and depends on
`sendMsg` for visibility. I made that line conditional, so on every normal reply the container
stayed `display:none` and **her words never rendered.**
**How it passed:** `npm run check` green, 22 unit tests green, both mutants caught. I audited the
nine WRITERS of `#sub-en` and never audited who makes the container VISIBLE. Two responsibilities,
conflated. **No test asked the only question that mattered: are her words on screen?**
→ CLAUDE.md **50**. Third instance of the same error, after backlog #170 and bugs.md 80.
**And he did not want the feature anyway** — *"there's always three dots anyway."* The `...`
already did the job. **I inferred a problem from a latency number instead of asking whether the
wait bothered him.**

### Also caught, before it shipped
Removing the `...` writes also removed the `const subEn`/`subEl` that a later line still used —
a `ReferenceError` inside `sendMsg`'s try on **every turn**. **`npm run check` went green**,
because it parses without resolving names. → CLAUDE.md **49**.

### Found, not fixed
- **First-message lag is real but unquantified.** Turn 1 prefill 1594ms vs 855-1004ms after. The
  trace does not capture Ollama's `load_duration`, so model-load vs prefill is unknown. Zani said
  to leave it. One line to add when someone picks it up.
- **CLAUDE.md 36 contains an inaccurate claim.** It says prewarm is "awaited to completion, so
  nothing overlaps playback". `Promise.race` does not cancel the loser, so a prewarm slower than
  4s runs DURING the boot video — the condition bugs 60/63 exist to prevent.

---

## September 6, 2026 (later) — measured the pipeline without talking to her, and found her voice is off

**New tool only (`dev/latency_probe.py`). No app file changed. NO REBUILD.**

### Zani's constraint shaped the tool, and he was right to set it
He asked for P1's numbers without holding 30 real conversations, **and asked that none of it be
written into her diary.** Driving her chat automatically is not a free substitute: every turn
enters `history`, is rolled into the diary on close, feeds `maybeExtractFacts()` (→
`amadeus_facts_v1`, injected into EVERY future prompt) and bumps the relationship score.
**Thirty synthetic turns would have become thirty false memories.** → backlog #192.

### ⚠️ The most important finding is not a latency number
**Fish Audio API credit is exhausted.** From turn 15 of 30 the API returned
`402 Insufficient API credit`. **Her voice is DOWN in the live app right now.** `ttsSpeak`
catches the 500, falls back to `startEstimatedReveal()`, and she goes silent with her words
still on screen and nothing on the UI to say why. Top up at fish.audio/app/developers —
**API credit is billed separately from platform credit.** → backlog **#191**.

### The numbers, n=14 complete turns (app CLOSED, idle machine)
| stage | median |
|---|---|
| RAG | 80ms |
| prefill | 598ms |
| to first token | 625ms |
| generate rest | 1036ms |
| translate (gemma4) | 1070ms |
| Fish | 1536ms |
| **TTS round trip** | **2673ms** |
| **TOTAL** | **4520ms** |
Prompt 4222 tokens · generated 37 tokens · reply 22 words — all matching the live app's ranges.

### The bias, stated before the numbers get quoted anywhere → backlog #193
Same prompt size, same day: the probe reads **598ms** prefill, the live app read **855–1004ms**.
**~1.6x.** The probe has no Live2D, no WebGL, no BGM, no Electron on the GPU that gemma4 runs on.
So it understates the wait, and it understates the **gemma4 stages specifically** — prefill,
generation and translate are GPU-bound; Fish is a network call and is unaffected.
**Use the probe for A/B and for proportions. Use P1's live numbers for any absolute claim.**

### What this says about P3 — the case keeps weakening
TTS is 59% of the probe's total, but it splits **translate 1070 / Fish 1536**, and translate must
run on the COMPLETE English text in every design that respects CLAUDE.md 37. Streaming can only
attack the Fish half. On live-app numbers that is roughly **0.7–0.9s off ~4.8s**, bought with a
permanent prosody seam, MediaSource and a subtitle rewrite (bugs.md 6).
**Meanwhile `translate` is a second gemma4 call costing ~1.07s serially, after generation has
already finished.** It is now the single largest gemma4 cost after generation itself, and nobody
has looked at it. That deserves its own item before P3 is bought.

### Two defects the first run exposed in the tool itself, both fixed
1. **The 'before' hash was taken AFTER importing `kurisu_rag_server`**, which re-upserts the 15
   static behavior rules at module level. `before == after` therefore looked like a clean proof
   while the file hash had in fact moved between runs. The baseline hash is now taken **before any
   import**, and the churn is printed and explained. **A safety proof that cannot see the thing it
   is proving is not a proof.**
2. **Turns whose TTS failed have a `total_ms` that excludes the TTS stage.** Mixing them into one
   median reported 3611ms when the complete turns were 4520ms — a 25% understatement, produced by
   a real outage. Complete and partial turns are now reported apart, with a loud warning.

### Verified
Chroma row counts identical across the run (`kurisu_ja` 756, `kurisu_en` 1672, `amadeus_diary` 56,
`amadeus_behavior` 15) and the sqlite hash unchanged. `/index-diary` was never called.
localStorage is unreachable from python, so her diary, facts and relationship score are untouched.
The probe refuses to run while the app is open.

---

## September 6, 2026 — P1's first live run: the instrument works, and it caught its own bug

**`amadeus.html` only — NO REBUILD. n=4, TEXT turns only. This is NOT a result.**

### It runs live, and two independent clocks agree
Zani relaunched and ran four typed turns. The trace recorded all four, closed every turn, and
printed a `[Perf]` line per turn. **The strongest evidence it is measuring reality:** on turn 4
the renderer measured a TTS round trip of **2859ms**, and the Fish server independently reported
`translate_ms 1430 + fish_ms 1420 = 2850ms`. **Two separate processes, two separate clocks, 9ms
apart.** That is the cross-check the design was built for.

### It immediately found a defect in itself → bugs.md 79
`latencyStatus()` printed `rag: null` for every turn. The mark was recorded fine (91–120ms);
the DELTA subtracted `stt`, which a typed turn never has. Fixed with a first-stage-only helper.
**Read the raw dump, not the summary** — this is bugs.md 77b's lesson landing a second time, and
it is why `latencyDump()` was requested alongside the medians.

### The provisional shape — n=4, do NOT act on this
| stage | median | share |
|---|---|---|
| RAG | ~103ms | 2% |
| think to first token (mostly prefill) | 1065ms | 22% |
| generate rest | 1371ms | 28% |
| TTS round trip (translate + Fish) | 2565ms | 53% |
| audio start | **3ms** | 0% |
| **total, you → her** | **4825ms** | |

**There is no single dominant stage.** TTS is the largest block at 53%, but it splits almost
evenly into translate (1256ms) and Fish (1176ms) — and **translate must finish on the complete
English text in every P3 design that keeps CLAUDE.md 37**. So streaming can only attack the Fish
half. Best case is roughly **0.7–0.9s off 4.8s, about 15–19%**, bought with a permanent prosody
seam, MediaSource, and a subtitle-timing rewrite (bugs.md 6).
**This is downside 7 from the P1 plan materialising: the honest early read is that there is no
cheap win.** At n=4 that is a hint, not a finding.

### Three facts the raw rows gave that the medians did not
1. **`evalCount` is 30–44 tokens against `num_predict:120`.** She is writing far short of the cap.
   **`num_predict` is not the constraint on her length** — the prompt is. This also means #176's
   "no range" shape is not a truncation artefact.
2. **`promptTokens` climbs every turn: 3884 → 3946 → 4048 → 4151.** History accrual. At ~4.1k she
   is at half of `num_ctx:8192`. **Prefill must always be read next to prompt size** — hence the
   two new fields in the report.
3. **Turn 1 prefill 1594ms, then 855 / 865 / 1004.** That reproduces bugs.md 68's live pattern
   (~1569ms cold, then ~850ms) almost exactly, on a different day and a different session.
   The KV prefix is being reused as designed.

### Still completely untested live: the VOICE path
All four turns were `kind:'text'`. **`stt` has never been exercised in the real app**, and the
voice path is where CLAUDE.md 48(b) bites — the clock opens at speech end and can die at the
Whisper gate or a VAD misfire. The unit tests cover those paths; the live app has not.
**Next run must include hands-free turns.**

### Verified before committing
41/41 unit tests (33 at commit time; 8 more added the same day for cross-launch persistence), and **the new test was proved to fail against the unfixed file** rather than
merely passing against the fixed one. `npm run check` 11/11. `SYSTEM_PROMPT` byte-identical to
HEAD by sha1. Test count reconciled 27 → 33 in CLAUDE.md, roadmap.md and backlog #186.

---

## September 4, 2026 — presence chosen as the direction; P1, its instrument, shipped

**`amadeus.html` + `kurisu_fish_server.py` — NO REBUILD, relaunch picks it up.
NOT yet live-verified: it touches TTS and the hands-free path, so it needs Zani.**

### The direction, decided by Zani
North star: **Jarvis-style real-time support, with Kurisu's personality, voice and appearance
kept exactly as they are.** Offered presence-first or awareness-first; **he chose presence.**
Scoped as P1–P5 → backlog **#186–#190**, roadmap section added.

### What the research changed
SOTA read before scoping (standing order). Two findings moved the plan:
1. **Barge-in is not an addition — it reverses a deliberate design.** `hfSubmit` calls
   `hfPauseListening()` the moment he stops talking, and the mic stays off until 600ms after
   her reply (`HF_RELISTEN_DELAY_MS`). Backlog #53 deferred barge-in on purpose. Industry
   target is <150ms; human turn-taking is ~200ms.
2. **Fish Audio has a WebSocket streaming TTS endpoint** (`wss://api.fish.audio/v1/tts/live`:
   streamed text events, `chunk_length` buffering, a `flush` command, latency modes).
   **Backlog #153 did not know it existed.** It removes both costs #153 called unfixable —
   the fixed per-call Fish overhead and the 30–100ms MP3 seam. → #188.
Also: **#153's Phase 0 is already answered.** It asked for a sentence count before building;
bugs.md 77b measured **3.23 sentences/turn**, putting her at the TOP of #153's 1.5–3s estimate.

### P1 — what shipped
One headline number per turn: **he stops talking → she starts talking**, plus the breakdown
(Whisper, RAG, prefill, first token, generation, translate, Fish, first audible sample).
- `latencyStatus()` / `latencyDump()` / `latencyReset()` in DevTools; one `[Perf]` line per turn.
- `kurisu_fish_server.py` now returns `timings:{translate_ms, fish_ms, translator}` from `/speak`.
- **No model call, no GPU work, no behaviour change.** Ring of 200 turns ≈ **50KB** localStorage
  (258 bytes/row, measured). The write happens AFTER her audio starts, outside the measured path.

### Downsides were minimised before implementing, not accepted
Zani asked for this explicitly. Four of the seven I had listed were designed out:
- **No new server endpoint and no new log file.** The first design POSTed each turn to a new
  `/perf` route on the RAG server. Dropped — it would have added a third changed file, a third
  server to relaunch, and a network call in the turn path. localStorage + `latencyDump()` does
  the same job with two files.
- **A kill switch instead of a revert.** `PERF_TRACE=false` + relaunch disables everything.
- **Cross-process clocks made impossible to mix.** The Fish server reports DURATIONS only;
  `time.perf_counter()` and `performance.now()` can never be subtracted from each other.
- **Text turns are measured too**, so the n≥30 threshold arrives sooner.
Three could not be removed and are stated plainly: it ships no felt improvement; it needs a real
evening of use before the medians mean anything; and it may report that no cheap win exists.

### The defect I found in my own first pass
The instrument opens a clock at speech end. I had covered the Whisper no-speech gate and VAD
misfires (`hfAfterDiscard`), **but not `sendMsg`'s two early returns** — `isLoading` and the
diary-save overlay. Either leaves the clock running, and the NEXT turn then reports a wait that
never happened. **Nothing on screen would ever show it.** Fixed, and the case is now test 9.
→ CLAUDE.md **48**, which also carries the second trap: instrumentation must never throw into
its caller, because `ttsSpeak` is deliberately not awaited so its failures cannot reach
`sendMsg`'s catch and run `history.pop()`.

### Verified before shipping
- `node dev/perf_trace_test.js` — **27/27**. It extracts the shipped block out of `amadeus.html`
  by anchor and evals THAT, never a hand-copied duplicate (bugs.md 77's byte-identical discipline).
  It drives the leak paths, a full localStorage, the kill switch and the ring cap.
- `npm run check` — 11/11.
- **`SYSTEM_PROMPT` proven byte-identical to HEAD** by sha1 (`393b669f…`), so nothing in her
  character moved.
- **The real `/speak` endpoint was exercised twice** through Flask's test client (app closed, no
  port bound, nothing left running) rather than reasoned about. Cold: translate 2987ms
  (gemma4, includes the model load) + Fish 379ms. Warm, 21-word input: translate **1195ms** +
  Fish **1208ms**. **n=1 — an instrument check, not a result.**

### Docs drift found and reconciled
- **Ollama is now 0.33.3** (read live, 2026-09-04) — it was 0.33.2 on Aug 31. **Three
  self-upgrades in nine days.** The 30-minute `keep_alive` default was measured on 0.33.2 and
  has NOT been re-measured on 0.33.3; CLAUDE.md 44 now says so.
- **`roadmap.md` claimed Amadeus Internet Research was ✅ shipped**, while its own detail section
  says the approach was abandoned. The code agrees with the detail section: `fetchWebContext`,
  `needsWeb` and `/web-search` are 0 hits, and git never contained them (the feature predates the
  July 13 baseline). Row corrected to ❌. **She has no live outside-world knowledge today** —
  which matters, because it is a real gap for the Jarvis goal.
- **CLAUDE.md 47's line numbers were wrong** (`:4904` pointed at a `catch` block; the real third
  greeting push had drifted to `:5203`). Replaced with the grep that finds them, because every
  edit above them shifts them again.
- Rule-count references updated 1-47 → 1-48 in `bugs.md` and this file's standing orders.

### Also corrected: backlog numbering
My code comments first cited "#185". **#185 was already taken** (the `main.js:610` disk-size
nit). Renumbered to **#186** across `amadeus.html`, `kurisu_fish_server.py`,
`dev/perf_trace_test.js` and CLAUDE.md before it spread further.

### Revert
Tags `pre-p1` and `post-p1`. `dist/` is gitignored, but **neither changed file needs a rebuild** —
`main.js:480` serves `amadeus.html` straight from the project directory
(`python3 -m http.server 8765`, `cwd: AMADEUS_DIR`), so a checkout plus a relaunch is a true revert:
```
git checkout pre-p1 -- amadeus.html kurisu_fish_server.py
```
Faster still, and no git needed: set `PERF_TRACE=false` in `amadeus.html` and relaunch.

---

## September 3, 2026 — the fix Zani asked for was aimed at the wrong phrase

**`amadeus.html` only — NO REBUILD, relaunch picks it up. NOT yet live-verified: needs Zani.**

### The requested fix had no target
Zani approved the backlog #177 "Hmph" fix. Measuring the baseline first killed it: **"Hmph" is
0/30 on tsundere probes**, 1/30 on daily-life — ~1.7%. **#177's premise was mine and it was
wrong**: I read bugs.md 76's *"hmph / it's not like / w-what stay ~90-100%"* as a rate for
"Hmph". It is the rate for the **group**. → CLAUDE.md **46**.

### What the same measurement found instead
**25/30 = 83% of flirty replies opened "W-what", on 3 distinct openers in 30.** More than twice
the 37% catchphrase bugs.md 76 treated as serious. Cause: `ROMANTIC/FEELINGS` item 2 **mandated**
a stammer *and* listed three. 13 sites supplied or mandated one; "W-what" alone at 4.

### The target came from the corpus, not from taste
Canon stammers on **3%** of lines, **0/64** of the lines the shipped retriever returns for those
same affection probes, and **42 of its 48 stammers are distinct**. Ours: 100% mandated, one form
at 83%. Wrong on **rate** and on **variety** — only the corpus could establish that.

### The fix: replace the LIST with a RULE for forming the thing
A list has three members and she picks the first. *"Build the stammer out of the word you were
ALREADY going to say — repeat its first sound"* generates a different result per sentence and
**supplies no phrase at all, so CLAUDE.md 43 cannot be violated by construction.** Plus mandate →
*"not every reply needs one"* and a session-scoped anti-repeat. **12 sites in one pass** — bugs.md
76 proved one survivor holds the rate steady. → CLAUDE.md **45**.

| metric | baseline | fix | p |
|---|---|---|---|
| opens "W-what" | **83%** | **37%** | **0.00048** |
| "I-I wasn't implying" | 20% | **0%** | 0.024 |
| flustered/tsundere tag **[GUARD]** | 100% | **100%** | 1 |
| deflects **[GUARD]** | 90% | **97%** | 0.61 |

### What it did NOT fix — stated because the headline flatters it
The "what"-family still opens **50%** of replies (canon: 1 line in 1,672); distinct openers
**7/30** vs canon's 34-in-64. **And I created a new crutch: `"Don't"` 13% → 33%**, because two of
my replacement exemplars both open on it — the old prompt's exact mistake, one iteration later
(→ backlog **#180**). Stammer rate fell 87% → 40%: intended (canon 3%), but it was declared a
guard before the run, so it is logged as a guard that moved. **Zani decides whether 40% feels
right — the metric cannot.**

### A second arm was measured and rejected
Adding a "vary the MOVE, not just the words" instruction (+241 chars) bought **nothing**
(p=0.60/0.80/0.78, all indistinguishable). The smaller arm shipped on prompt-budget grounds.
**Do not re-run it.**

### Verified before shipping
The shipped `SYSTEM_PROMPT` was extracted back out of `amadeus.html` and proven **byte-identical
to the measured arm** against `git show HEAD:amadeus.html`. `npm run check` 11/11. Mirror
reconciled in `kurisu-personality.md` (it carried the old text at 8 lines).

### Left alone on purpose
8 hand-written canned strings still contain "Hmph"/"W-what". They are Zani's content, not a model
bias. **But `amadeus.html:973` pushes the chosen greeting into `history`**, so canned text acts as
an in-context exemplar all session → CLAUDE.md **47**, backlog **#179**.

### Measurement anomaly — SOLVED, and my first diagnosis was wrong
I reported that arm B's 1222s wall "was not in the Ollama calls, since per-call times sum to ~60s".
**Wrong — I had only read the last three lines of the log.** The stored `.json` shows two calls at
**933.4s and 242.0s**; per-call wall sums to 1220 of the 1222s. The real defect was that the summary
*hid* the outliers, so a 20-minute arm looked normal. Fixed. → bugs.md **77b**.

### Self-review found two more faults of mine (bugs.md 77b)
The "deflects" guard was **circular** — 8 of its 16 markers are in the shipped prompt, 5 of them in
text this very fix introduced. The tag guard (100%) is independent and is the one to trust. And
there was **no everyday-chat control**: the fix edited a CASUAL rule and I measured only flirty
probes. That gap is now closed — see below.

### #181 — everyday-chat regression control: CLEAN
n=30 per arm, BEFORE read from `git show 8b0b953~1:amadeus.html` (the real shipped prompt, via a new
`--prompt-rev` flag). Length distribution 9.89 → 8.54 W, **KS p=0.24 — no change**. Sentences/turn
**3.23 → 3.23**. Stammering did **not** leak into everyday chat (0/30 both). Questions, tags and
opener variety all unchanged. **It also partly restores #176's lost reproducibility**: the BEFORE
arm re-creates the daily-life baseline at W 9.89 against the 9.15 recorded — inside the noise floor.

### Then Zani hit a bad reply in normal use, and the capture rewrote the plan
He caught *"Now that we've established the **parameters** of literary archetypes"* on the casual
input *"that's all I need to know"*, and dumped the turn log. Three causes, all pre-dating
bugs.md 77 and all visible in the same prompt: (a) **`parameter` is on the CASUAL banned list** —
the only banned word in all 7 turns, in exactly that reply; (b) she entered ACADEMIC mode for
*"what does tsundere mean"*, which is **not** science/philosophy/logic, and **there is no rule for
leaving it** — her own academic turn then sat in history as an exemplar; (c) two pre-fix clinical
diary entries were retrieved into that turn. → backlog #183.

### A write-gate was approved, and measuring killed it
Zani approved a diary write-gate. Deduplicated and split at bugs.md 69's ship date: clinical
entries **27% before → 0/6 after**. **bugs.md 69 works and the gate would have fixed nothing.**
An earlier "5/10 recent entries clinical" reading of mine was wrong — triplicated rows plus a
false positive on *baseline* used normally. → backlog #182. **Read the rows; a keyword classifier
is a screen, not a verdict.**

### What was actually broken: 30% of her memory was duplicate rows (bugs.md 78)
`/index-diary` keyed rows by ARRAY POSITION when dates collided, and entries are `unshift()`ed —
so every position shifts on each write and `upsert` created a new row. **79 rows for 55 entries,
one stored 5 times**, under consecutive ids `entry_17..21`. Retrieval returns nearest matches, so
**a memory stored 5x was 5x more likely to reach her prompt** — silently amplifying the very
#161 entries caught in the capture. Fixed with content-derived ids plus a one-off migration.
**The skip test is on TEXT, not id, on purpose:** skipping by id would have inserted 50 fresh
copies on the first launch after the change. Bonus: a normal launch now embeds **0** entries
instead of all 50, fire-and-forget on the GPU during boot (CLAUDE.md 36/37).
All of it verified on an isolated COPY: 0 texts lost, 0 added, 55/55 dates kept, idempotent, and
0 inserts against BOTH a migrated and an un-migrated database.

### New tool: `dev/prompt_lint.py`
The check that would have caught my own "Don't" mistake mechanically. Pure CPU, <1s. Compares every
quoted phrase and every exemplar opener against canon, splits quoted-to-SAY from quoted-to-FORBID,
and **normalises stammer prefixes** — without which `"D-don't"` and `"don't"` look like different
openers and it misses the exact bug it exists to catch. Reports `"don't"` at 3/38 exemplars vs 2.2%
of canon (#180), plus newly found: `you` opens **21%** of exemplars vs 3.9% of canon.

---


## August 31, 2026 — the canon gap, measured. My leading hypothesis was wrong.

Goal: make her sound more like the show. Zani's instruction was **measure the gap first,
do not pick an intervention**. Nothing shipped to the app. **No code changed, no rebuild.**

### What "sounds like the show" means here, decided BEFORE scoring
Zani chose the headline metric: the **word-count distribution** against the 1,672-line
`kurisu_en` corpus. Vocabulary overlap and tic rates were offered and declined as headline
axes — they print as diagnostics only. Win condition: canon-likeness is the proxy, **Zani is
the referee**; nothing ships on the metric alone.

### Tools, both in `dev/`
`canon_likeness.py` (scorer, `--validate` / `--score` / `--compare`) and `canon_gap_probe.py`
(generates replies from the byte-exact `SYSTEM_PROMPT` + live RAG, in the shipped
`RAG_AS_TAIL_MESSAGE` layout). Pure CPU for the scorer. **The probe calls gemma4 once per
reply — never run it with the app open (CLAUDE.md 37).**

### The metric was validated before it was trusted
Canon-vs-canon split-half: W≈0.77, 19/20 indistinguishable. Assistant-speak and a degenerate
all-3-word arm are both rejected. **And it produced the number that binds every future run:
at n=30 the noise floor is W≈4.99.** Below ~5 words at n=30, a difference is not real.

### The gap (n=30, daily-life probes = the #162 worst case, RAG on)
**W = 9.15 words from canon, KS p = 1.8e-08** — roughly twice the noise floor.
**0% of her replies are ≤8 words; 50.8% of canon's are.** Median 17 vs 8. Longest 22 vs 114.
3.13 sentences per turn vs 1.79. 87% contain a question vs 36%.
**She has no range** — clamped to a 13–22 word, three-sentence, question-ending shape. The
"under 35 words" cap is not the binding constraint; nothing came near it. Per *sentence* she
is nearly canon (W=1.25–1.87), so her sentences are fine and she stacks too many per turn.

### The negative result, which is the point of the day
I replaced **all 38** hand-written exemplars with real VN lines, stratified to inherit canon's
own spread, tag sequence held byte-identical. **W 9.15 → 9.56. A vs B, KS p = 0.39 — no
detectable difference.** Still 0% short replies.
**The exemplar block does not control her output shape.** My opening hypothesis and the
previous handoff block both predicted it did. Both wrong. → **backlog #176, "do not re-run".**
This does NOT contradict bugs.md 76: exemplars transfer *phrases* strongly and *shape* not at
all. Two mechanisms. Do not reason from one to the other.
Supporting evidence that the residue is model-side: `"Seriously"` 20–23% of her replies vs
**0.5% of canon**, `", huh"` 13–17% vs 3% — and **neither string occurs anywhere in
`SYSTEM_PROMPT`** (0 grep hits), and both survived the swap. That is gemma4's own register.

### Found, not fixed
- **backlog #177 — `"Hmph."` is quoted twice in the prompt and appears 0 times in 1,672 canon
  lines.** Exactly the bugs.md 76 configuration. bugs.md 76 had filed "hmph" under *"deflection
  IS the character"* **without checking the corpus**. Must be measured on tsundere probes, not
  daily-life ones (1/30 there) — the off-topic-probe trap again.
- **backlog #161 is live, not theoretical.** A plain *"did you eat dinner"* retrieved
  *"threw my processing unit into an inefficient state"* and *"his 'biological hardware'"*
  from the pre-fix diary entries still sitting in the `amadeus_diary` collection (79 docs).
- **backlog #178 —** she emitted `[concerned]`, an invalid tag, 1/30. Falls back silently.

### Also settled today (committed separately, `8eea014`)
**Ollama upgraded itself to 0.33.2**, five days after it went 0.21.0 → 0.32.15. On 0.33.2 the
default `keep_alive` is **30 minutes, not 5** — measured directly. bugs.md 75's fix is
therefore redundant *on this version* and load-bearing again the moment the default moves back;
nothing in it is retracted. CLAUDE.md 44 restated in those terms. **Live-test caveat: if the
first-message stall is gone, the version change is an alternative explanation — confirm via
`/api/ps` `expires_at` with the app running, not by absence of the symptom.**

### Fine-tuning: deferred by Zani to a future session
Costing was started and stopped on his instruction. The one hard number gathered before
stopping, worth keeping: the EN corpus is **1,672 lines / 21,029 words / ~28k tokens**, and it
contains **only Kurisu's lines — no speaker column, and not the turns she is replying to**.
So it is not instruction-pair shaped as it stands. #175's JA↔EN alignment was spot-checked and
**its "offset ~5" holds at the head and at the very end but NOT in the middle** (checked at
25/50/75%) — the monotonic DP #175 proposes is genuinely required, and #175's own instruction
to "verify the offset holds across the whole file" now has an answer: it does not.

---


## August 26, 2026 (final) — two issues Zani found by using her: GPU stall, and a catchphrase

Both fixed. **`kurisu_rag_server.py` + `amadeus.html` — no rebuild, relaunch picks both up.**

## Issue 1 — ~2s lag and Live2D stutter on the first message (bugs.md 75)

**Root cause: bge-m3 was unloading after 5 minutes.** Every gemma4 call in the app passes
`keep_alive:'30m'`. The RAG server's embed calls passed **nothing**, so Ollama's 5-minute
default applied — and the server's own startup warm-up expired 5 minutes after launch. The
first RAG query after that reloaded the model on the GPU that renders her.

**Cold embed 812 ms vs warm 10 ms — 81x**, spent before a single token streams, so the screen
shows nothing while the animation stutters. Confirmed by reading `/api/ps` `expires_at`
directly rather than inferring: gemma4 30.0 min, bge-m3 5.0 min. After the fix, 30.0 min.

**Why it hid:** it needs a >5-minute gap between the RAG server starting and the first
message — the normal launch-and-settle pattern, and never what happens while developing and
testing in quick succession.

**A first hypothesis was measured and demoted rather than shipped.** The greeting's TTS
translation runs through gemma4 and does evict the prewarmed chat prefix — but only
**138 ms → 287 ms** (n=30). Real, and **5x smaller** than the 812 ms. Fixing it means touching
boot timing, where bugs 60/62/63 all regressed, so it is backlog **#174** with constraints
and a cheaper alternative to price first. Chasing it would have fixed ~15% of the problem.

## Issue 2 — "Don't get the wrong idea" in 37% of replies (bugs.md 76)

**It is not her character — our prompt was teaching it.** The phrase appears **once** in the
2,522-document RAG corpus, and that hit is *her own diary entry* echoing it. The 1,672 lines
of real Kurisu VN dialogue never say it.

The prompt quoted it **twice**: as an example of tsundere output in the INPUT→EMOTION rule,
and as a crutch to avoid in the anti-crutch rule. **Naming a phrase to forbid it still supplies
it.** The anti-crutch rule was also too weak by construction — it banned only *"twice in a
row"*, so every second turn was compliant. That is precisely what "repetitive but not
consecutive" feels like.

| arm | "wrong idea" | p |
|---|---|---|
| A baseline | **11/30 — 37%** | — |
| B fix INPUT→EMOTION only | 12/30 | 0.70 |
| D fix anti-crutch only | 10/30 | 0.50 |
| **C both** | **3/30, then 1/30 fresh** | **0.0012** |

**Neither half works alone — that is the result.** Each line quotes the phrase, so fixing one
leaves the other naming it. **The phrase must be absent from the entire prompt; one mention
anywhere holds it at ~35%.** An A/B that changed a single site would have read "no effect"
and shipped nothing.

**Her character was measured, not assumed:** still deflects **30/30**, tsundere tag **30/30**,
in every arm including the fix. She deflects exactly as often, in different words. Distinct
openers 17/30 → 20/30. A variant that had reduced deflection would have been rejected the way
the bugs.md 71 first-person summary was.

**Honest limit:** other stock deflections (hmph / it's not like / w-what) stay ~90-100% in
every arm. That is deliberate — deflection IS the character. Only the dominant catchphrase
was targeted.

## Two rules added
**CLAUDE.md 43** — never quote a phrase you don't want her to say, not even to forbid it;
describe the behaviour, and remove it from EVERY site or the A/B will read as no-effect.
**CLAUDE.md 44** — any model the app depends on interactively must state its own `keep_alive`;
Ollama's default 5 minutes is shorter than a user's think-time.

## What both issues have in common
Neither was findable by reading code, and neither showed up in any test suite. **Both needed
Zani to use her normally** — one needs a five-minute pause, the other needs enough turns to
notice a rhythm. That is the third time today that live use beat static reasoning.

---

## August 26, 2026 (end, later) — self-review: my own fix had made something worse

Zani asked for a review of the session's implementations. One real finding, in the code I
had written hours earlier. **`amadeus.html` only — no rebuild.**

### The finding
CLAUDE.md rule 37 requires every background gemma4 caller to be **(a) idle-gated AND (b)
abortable via `noteActivity()`**. `extractFactsNow` had (a) and not (b) — no
`AbortController`, and absent from `noteActivity()`, which aborted only `proactiveAbort` and
`_warmAbort`. Its own comment asserted the design was safe: *"the idle gate alone decides
when it actually runs, which is what protects the GPU."*

**A gate is not a brake.** A gate decides when work starts. Once started, that extraction ran
to completion regardless of what Zani did — saturating the GPU that renders her, and evicting
the chat KV prefix, while he waited for a reply.

### Why it is partly self-inflicted
The gap pre-dated today. But **bugs.md 73 raised this exact call's `num_predict` 300 → 500**,
lengthening the un-interruptible window:

| cap | un-abortable GPU window (n=10, wall clock) |
|---|---|
| 300 (before 73) | median 6.68s, max 8.48s |
| 500 (after 73) | median **8.52s**, max **9.66s** |

I reviewed that cap change against rule 40 (truncation) and never against rule 37. **A
correctness fix quietly degraded a responsiveness property.**

### Fix, and the trap inside the fix
An `AbortController` on the fetch, cleared in `finally`, aborted from `noteActivity()` —
mirroring `_warmAbort`.

The trap: a naive abort would **discard the harvest**, re-introducing the silent fact loss
bugs.md 73 had just removed, from the opposite direction. So the `AbortError` branch sets
`_factsDue=true` and re-arms `scheduleFactsExtraction()`, and logs distinctly from a real
failure. Yielding the GPU now costs latency, not memory.

### Verified — including the part that is easy to fake
- Structure 7/7, read from the shipped file.
- Client releases: heavy call **14.14s** unaborted → **1.01s** aborted at 1s, `AbortError`.
- **The GPU is genuinely freed, not just the client.** A tiny probe issued immediately after
  the abort returned in **69 ms** against a **119 ms** idle baseline — not queued behind a
  still-running generation. *This is the check that matters:* a client that stops waiting
  while the GPU keeps working would look fixed and change nothing.

### Logged, not fixed
`studyTick` is the fourth background caller named in rule 37 and has no abort either — two
gemma4 calls per tick, one of them vision with a screenshot attached. Untouched this session,
so it is backlog **#173** with a measure-first instruction rather than a change made tired at
the end of a long session.

### Rule added to CLAUDE.md 37
Gated and abortable are different properties, both required; "abortable" means the GPU is
released, verified with a probe; re-queue work an abort would discard; and **any change that
makes a background call longer must be re-checked against rule 37, not only rule 40.**

---

## August 26, 2026 (end) — #172: the machine-safe anchor was a disk size

**Measurement only — no code changed.**

The standing order says every new component must fit "the M5/16GB resource budget (gemma4
~9.6GB is the anchor)". A live `/api/ps` reading of 3.24 GB earlier today did not match it,
so the number every build decision is costed against was undefined.

### Resolved: three numbers, one of them a RAM budget

| number | value | what it actually is |
|---|---|---|
| `ollama list` SIZE | **9.6 GB** (8.95 GiB) | the model FILE on disk. **Not memory.** |
| `/api/ps` `size_vram` | 3.02 GiB | Ollama's own accounting — *below* the real process footprint |
| **`llama-server` RSS** | **4.10 GiB** | **the resident cost. Use this one.** |

`ollama list` is where "~9.6GB" came from. It was transcribed correctly and is simply the
wrong kind of number: the model is **memory-mapped**, so the 8.95 GiB file is not resident —
file-backed pages sit in the evictable page cache.

Confirmed it is not a lazy-load artefact: RSS went **4.10 → 4.11 GiB** across a 1,089-token
prompt plus a 400-token generation. Machine verified as Apple M5, `hw.memsize` = 16.0 GB.

### Consequence
The standing order has been pricing new components against a figure **~2.3x larger than the
truth**. There is materially more headroom than assumed.

**Do not spend it yet.** gemma4 is one line of the budget, not the total — the four Python
servers (Fish TTS, RAG + bge-m3 ~1 GB, Whisper large-v3-turbo) and Electron were not running
when this was taken. That measurement is the remaining half of #172 and is cheap: launch the
app, then `ps -Ao rss,comm | grep -Ei 'llama-server|python3|Amadeus'`.

### Why this one mattered more than its size suggests
It is not a bug in the app — nothing behaved wrongly. It is a bug in the **decision rule**.
Every "does this fit?" judgement since July was made against it, and the answer to that
question was wrong by more than a factor of two in the conservative direction. Being wrong
conservatively costs opportunities rather than crashes, which is why nothing ever surfaced it.

Corrected in CLAUDE.md (the standing order itself), REFERENCE.md (a table of all three
numbers, so the next person cannot pick the wrong one), and roadmap.md.

---

## August 26, 2026 (late) — backlog #159 measured: the prose paths were fine, the fact extractor was not

**`amadeus.html` only — no rebuild. Relaunch picks it up.**

### #159 asked a question; the answer was no
It flagged the unguarded `stream:false` paths as needing the bug-67 truncation guard, and
gated itself on "do this once truncation actually happens in practice". Measured with the
real `SYSTEM_PROMPT`, real history and the real directives, n=30 each:

| path | cap | tokens med / max | truncated |
|---|---|---|---|
| `fireProactive` | 80 | 19 / 27 | 0/30 |
| `studyTick` remark | 80 | 18 / 24 | 0/30 |
| `checkDMails` | 120 | 20 / 36 | 0/30 |

**0/90.** These ask for "one short line" and get ~4x headroom. Adding the guard would have
been code with no defect to fix. #159 is closed as **measured-not-warranted**, with the
numbers recorded so nobody reopens it on reasoning alone.

### The same sweep found a real defect (bugs.md 73)
The JSON paths were checked next, because they fail differently. `extractFactsNow` at
`num_predict:300`, worst case (60 known facts + a fact-dense conversation): **10/30 = 33%
truncated**. In JSON mode a truncation is not a shortened result, it is an **unparseable**
one — `JSON.parse` throws, the catch logs a warning, and **every fact from that cycle is
discarded**. Facts are injected into every prompt.

| cap | facts lost |
|---|---|
| 300 (was) | 10/30 |
| 400 | 1/30 |
| **500 (now)** | **0/30**, 431-token max |

A typical conversation uses 66 tokens median and was never at risk. A cap costs nothing
until it is reached, so the common case is unchanged.

**Fail-closed was already correct — and that is exactly why nobody noticed.** All three JSON
callers parse inside `try` and validate before use, so truncation could never corrupt
memory, only lose it. *Fail-closed and silent are the same thing without telemetry.*

### The rule all three of today's truncation findings share
**Risk is the ratio of what the prompt ASKS FOR to the cap, not the cap's absolute size.**

- "3-4 sentences" at 100 → ~0.8x → **63%** truncated (bugs.md 70)
- an unbounded JSON list at 300 → ~0.8x → **33%** (bugs.md 73)
- "one short line" at 80 → ~4x → **0/90** (#159)

Now CLAUDE.md rule 40.

### A process note worth keeping
The final sizing run was oversized and **was killed at the 10-minute command cap**: 90
generations at 500-600 output tokens, when every earlier run in the session had been ~3s per
call at ~100 tokens. The per-call cost was carried over as an assumption instead of being
re-estimated when the output length changed by 5x. No harm — the decision was already
covered by data in hand, and the extra arm was dropped rather than retried. **Budget
measurement runs by output tokens, not by call count.**

### Not live-tested
This path runs in the background every 6 exchanges. Raising a cap cannot break parsing that
already succeeds, and the common case is unchanged — but it has not been observed in the app.

---

## August 26, 2026 (night) — all three fixes live-verified on the second attempt

Zani re-ran the close test after bugs.md 72 shipped. **All three pass.**

| check | result |
|---|---|
| 72 — the gate reopened | watermark `50` → **`c8e364f1b6441457`** |
| 70 — ends in a complete sentence | **PASS** |
| 71 — no case-file register | **PASS** |

### What actually changed, in her words
**Frozen (602 chars, third person):**
> *"…the **diarist** repeatedly finds herself… an 'utterly indifferent' **façade**… Ultimately, the entries suggest that despite"*

**Regenerated (584 chars, first person):**
> *"**I** keep finding myself reacting to Zani's casual touches… his genuine curiosity or unexpected thoughtfulness manages to chip away at **my** composure… in ways that feel wildly illogical and profoundly inconvenient to **my** usual detached routine."*

The old text described her **in the third person as "the diarist"** — a clinician writing
about a patient. The new one is her. And it stayed recognisably Kurisu (*"wildly illogical
and profoundly inconvenient"*), which is precisely what the rejected first-person variant
failed to do: that one scored a perfect 0% on register by hollowing the content out.

### How strong is this verification, honestly
- **72 is solid.** A watermark going from `50` to 16 hex is a binary state change, not a
  sample. The gate that had been shut since he reached 50 entries is open.
- **70 and 71 rest on one sample each**, plus the offline figures (63% → 0%, 97% → 7%). One
  good summary is consistent with the fixes, not proof of them — same standing as the single
  diary entry that verified bugs.md 69.

### Observation, n=2, deliberately not acted on
Both the frozen summary and the new one open their **final sentence with "Ultimately,"**.
bugs.md 65's opener anti-repetition applies to diary entries, not the rollup. Two samples is
not a pattern — recorded so a future session with more samples can decide.

### The day's lesson, restated
The first test attempt **failed**, and that failure was worth more than either fix. It
falsified a claim I had reasoned from the code path, written into a plan, a docs pass and a
commit message: *"self-healing, no migration."* Two correct fixes had been sitting behind a
gate that could never open.

---

## August 26, 2026 (evening) — the live test found that BOTH day's fixes were unreachable

Zani ran the bugs.md 70/71 close test. **It failed, and that is the most useful thing that
happened today.** `main.js` + `amadeus.html` → rebuilt.

### What he saw
`entries: 50 | watermark: 50` — **identical before and after** a full chat → close →
relaunch cycle. Summary byte-identical, 602 chars, still ending *"...the entries suggest
that despite"*. No `[main:diary-summary]` lines in the terminal.

### Why
The diary is **capped at 50** (`amadeus.html`, three `unshift`/`pop` sites). The gate was
`entries.length > watermark`, watermark stamped as `entries.length`. At the cap the length
is pinned at 50, so **`50 > 50` is false forever** and the summary freezes permanently.

**Both of today's fixes were correct and neither could ever run on his machine.** A perfect
generator behind a gate that never opens produces nothing.

### The claim this kills
bugs.md 70 said *"Self-healing, no migration — corrected on his next close."* I reasoned
that from the code path. It is true **only below the cap**, and Zani was at it. The claim
survived a written plan, a self-review, a docs pass and a commit message; **one live test
killed it in a single reading.** It is struck through in bugs.md 70 rather than deleted,
and the same wording is struck in backlog #165.

> **A code-path argument about long-lived state is a hypothesis, not a verification.**

### Fix
The watermark becomes a **fingerprint of the exact text fed to the summariser** (sha1,
16 hex), and regeneration happens when that fingerprint changes.

A fingerprint rather than a larger counter because a count cannot see the cap — and cannot
see an entry being edited or deleted either, both of which change what she remembers while
leaving the length untouched.

Migration needs no data touch: the renderer stops `parseInt`-ing the value and passes it
through, main.js compares strings, and `"50"` cannot equal 16 hex chars — so it mismatches
once and regenerates. At the cap it now regenerates every close, which is correct: each
close genuinely changes the older set.

### Verified 13/13
`dev/watermark_test.js`, gate logic extracted from the shipped `main.js` at run time. Covers
Zani's exact live state, idempotency, a new entry at the cap, edits inside vs outside the
window, null/undefined/empty watermarks, pre-cap growth, fingerprint shape, and the
numeric/fingerprint non-collision that makes the migration safe.

### Also: my test snippet gave a false PASS
Its case-file regex had plain `facade`; the stored text has **`façade`** with a cedilla. It
also missed *"the diarist"* and *"emotional leakage"*. The summary was a clear bugs.md 71
failure being reported as PASS. The re-test snippet below is corrected — but the real check
is still Zani reading it and saying whether it sounds like a person.

### Re-test — still owed, now three fixes on one close
Chat, quit, relaunch, then:

```js
(() => { const s=localStorage.getItem('amadeus_diary_summary')||'', d=JSON.parse(localStorage.getItem('amadeus_diary_v1')||'[]'), w=localStorage.getItem('amadeus_diary_summary_watermark'); const CASE=/exhibits|underlying|validation|reliance on|fa[cç]ade|the diarist|leakage|cognitive|mechanism|demonstrates|indicative|propensity|physiological|biological|optimal|efficien|parameter/i; console.log('entries:',d.length,'| watermark:',w); console.log('72 regenerated  :', /^[0-9a-f]{16}$/.test(w||'')?'PASS':'FAIL'); console.log('70 full sentence:', /[.!?\u2026]["\u2019\u201d')\]]?$/.test(s.trim())?'PASS':'FAIL'); console.log('71 case-file    :', CASE.test(s)?'FAIL -> "'+s.match(CASE)[0]+'"':'PASS'); console.log('\n'+s); })()
```

**bugs.md 72 is the gate: if `watermark` is still `50`, nothing ran and 70/71 are still
untested.** A 16-hex watermark means the summary actually regenerated.

---

## August 26, 2026 (later still) — bugs.md 71: her long-term memory was a case file

Backlog #168. **`main.js` → rebuilt.** Shares bugs.md 70's pending live close test.

### The same bug as 69, in the generator nobody looked at
bugs.md 69 fixed the DIARY's register. The stage-2 summary generator was never touched,
and it had the identical defect: no vocabulary constraint, output injected into **every**
prompt as LONG-TERM IMPRESSIONS. CLAUDE.md rule 42 already said this applied to "any future
memory/summary/fact text" — the words were there, the code was not.

**It was worse than the diary on both axes.** A diary entry ages out of the 7-entry window;
the summary sits in the prompt until the next diary write. And the rate was not comparable:

| | register failures |
|---|---|
| diary, before bugs.md 69 | 17% |
| **summary, before this** | **93%, and 97% on a fresh run** |
| summary, after | **7%** |

Fisher one-sided **p < 0.00001**, replicated on fresh samples.

### The finding that mattered most: my own banned-word list found nothing
The bugs.md 69 terms — *biological*, *physiological*, *calibrate*, *optimal* — scored
**0/30 in every arm, including the untreated baseline.** If I had measured only what the
previous fix measured, I would have concluded there was no problem here.

The actual failure vocabulary is different: not lab prose about biology, but **case-file
prose about a person** — *"exhibits"*, *"underlying anxieties"*, *"validation"*,
*"reliance on"*. That broader measure was defined from observed baseline output, which
makes it post-hoc, so it was **re-run on fresh samples** with the list frozen. 93% → 97%
on the repeat: it replicated.

### The variant I rejected, and why it is the important part of this entry
A stronger version also dropped the *"You are Kurisu Makise's memory system … about Zani"*
framing in favour of first-person recall. On the metric I was optimising it was **perfect —
0/30**.

It also **halved what she remembers**: themes carried fell 4.4 → 2.1, and some summaries
carried **none at all**. It scored perfectly by saying less.

That is only visible because content was measured alongside register — ten themes actually
present in the entries, scored per summary. The shipped version: 3.97 → **4.47**,
permutation two-sided **p = 0.186**, i.e. no detectable loss, and denser per character. A
comment in `main.js` now warns the next person not to "improve" this by making it more
first-person.

### Verification
- Banned-word sentence and substitutions copied **verbatim** from `buildDiarySystemPrompt()`;
  only the framing sentence adapted, because a rollup is not "a private journal entry".
- The shipped string was extracted back out of `main.js` and compared to the measured arm:
  **byte-identical**. (The first comparison failed because my extractor grabbed the `'system'`
  role literal — my bug, not a mismatch.)
- `npm run check` now genuinely covers this file — the #170 fix from an hour earlier paid for
  itself immediately.
- Cost ~135 prompt tokens on one call at close. Truncation stayed 0/30 at `num_predict: 180`
  with the longer prompt, so bugs.md 70 is unaffected.

### Rules checked by number
13, 17/18, 33/34/51, 40/70, 42/69, 55b, 57 — none violated. Chat KV prefix untouched.

---

## August 26, 2026 (later) — backlog #170: the pre-launch gate could not see the main process

Follow-on from bugs.md 70, which exposed the hole. **`dev/check.js` only — no app change,
no rebuild, nothing about the pending bugs.md 70 close test is affected.**

### The hole
`npm run check` read `amadeus.html`, `call-window.html`, the four Python servers and the
SYSTEM_PROMPT anchors. It never read `main.js` or the preload scripts. So this morning's
change — **100% in `main.js`** — got a green *"All checks passed — safe to relaunch"* from
a gate that had not opened the file. `npm run build` only packages; it does not parse.

The failure mode is the worst one this app has: a main-process syntax error is not a broken
feature, it is **no window and no boot video**, with nothing on screen pointing near the
cause. The gate was blind exactly where blindness costs most.

### The fix
`checkNodeFiles()`, new result kind `'js-file'`, covering **`main.js`, `preload.js` and
`preload_call.js`**. That third file because `call-window.html` was already checked, and
checking a window but not the script Electron injects into it is a gap of the same shape.

`'js-file'` is a separate kind from `'js-syntax'` deliberately: the self-test asserts a
mutant is killed by *its own* check, and this file already treats "right answer, wrong
reason" as a failure. Real files also mean node's own line numbers are correct, so none of
the inline-script line remapping is needed.

Cost ~90ms. The check now reports 11 results, up from 8.

### The new coverage is proven, not assumed
Three mutants added to `check.selftest.js`:
- **`main-js-syntax`** and **`preload-js-syntax`** — both must be killed by `'js-file'`
  specifically. The second exists because a loop that stopped after the first file would
  pass without it.
- **`shadowed-const-in-main`** — a second EQUIVALENT mutant, which must **not** be reported:
  a `const` inside a function shadowing a top-level binding is legal JavaScript. It blocks a
  plausible future "improvement" — CLAUDE.md rule 3 is about duplicate consts in ONE scope,
  and anyone strengthening this checker with a naive identifier grep would break every
  main-process launch.

Self-test: **7/7**, control run 11 checks.

### Meta-verified — the step that actually proves it
A passing self-test does not prove the new mutants depend on the new check. So the
`checkNodeFiles` call was removed from a **copy** of `check.js` and the self-test re-run
against that copy: it correctly reported `main-js-syntax SURVIVED` and exited 1. The
mutants have teeth for the right reason. The real `dev/` was never touched.

### Docs reconciled
The claim *"`npm run check` does not parse main.js"* was written into **five** places
earlier today, and this change made all of them false. All updated: the CLAUDE.md Commands
note now states the opposite, the roadmap gate description, the bugs.md 70 gate warning
(marked SINCE FIXED rather than deleted — it is why #170 exists), and the handoff trap. The
two mentions inside the bugs.md 70 session entry were left as history with a pointer, since
they record what was true while that work happened.

**New standing rule, in the handoff traps:** if you add a check, add a mutant for it in
`check.selftest.js` in the same commit.

---

## August 26, 2026 — bugs.md 70: the long-term memory was a fragment, 63% of the time

Backlog #165, shipped. `main.js` changed, so the app was **rebuilt**. **The live close
test is still owed by Zani** — this entry does not claim the fix is verified in the app.

### What was wrong
The stage-2 rollup asked gemma4 for "3-4 sentences" with `num_predict: 100` and stored
whatever came back, with no completeness check. The fragment went into
`amadeus_diary_summary` and then into **every prompt** as LONG-TERM IMPRESSIONS. Zani's
`dumpLastTurn()` capture caught it ending *"Ultimately, the entries suggest that despite"*.

### It was not a rare event
| `num_predict` | truncated (n=30) |
|---|---|
| 100 (old) | **19/30 — 63%** |
| 180 (new) | **0/30** |

Fisher exact one-sided **p = 2.7e-08**. Roughly two of every three summaries were fragments.

### A measurement gap I had left open, then closed
The first run used a 12-entry input. The real worst case is **43** older entries (the
diary caps at 50, the window is 7) = **1,755 prompt tokens**. Re-measured there: still
0/30 truncated, 132 tokens max (~27% headroom under 180), **3.70s max warm** against the
12s `SUMMARY_FETCH_TIMEOUT_MS`. One 10.37s outlier was the model *load* — and it cannot
happen on this path, because the summary call only runs after a successful diary call, so
gemma4 is always warm by then.

### The design decision Zani pushed back on, and where it landed
My first plan was to copy `trimToLastSentence()` into `main.js`. He asked why not trim
renderer-side and reuse the already-tested function, and pointed out its bail-out
thresholds were tuned for 120-token chat replies.

That second point decided it **against my original plan**. The two cases have opposite
trade-offs: a chat reply's fragment was **already spoken aloud**, so keeping it beats
losing 60% of what she said. Nothing here is spoken, and a summary fragment costs every
prompt until the next close. So the guard is a **purpose-built** function that trims
willingly and returns **`null`** rather than store something unusable — falling into the
existing `if (summaryText)`, which guards both the IPC send and the watermark advance, so
a refusal keeps the previous good summary and retries next close.

His drift objection was the strongest argument against a second copy — and it was real,
since the stale fallback prompt fixed in this same commit is exactly main.js duplication
going stale. It dissolves only because the rules deliberately differ: there is nothing to
keep in sync.

### Two defects found by reviewing the plan before writing it
1. **`npm run check` does not parse `main.js`.** *(Fixed later the same day — backlog #170,
   see the entry above.)* The change was 100% in that file, and the
   gate printed "All checks passed — safe to relaunch" having never read it. A typo would
   have been a main-process crash at launch: no window, no boot video, no clue. Ran
   `node --check main.js` by hand. → backlog **#170**.
2. **Gating the trim on `done_reason` was brittle.** Trimming well-formed text is a no-op,
   so the guard now runs unconditionally — which also catches EOS mid-sentence and drops a
   dependency on a field whose shape already moved 0.21.0 → 0.32.15. `done_reason` is read
   for the log line only.

### Verification
- **Unit 21/21** — `dev/trim_summary_test.js`, run against the function **extracted from
  the shipped `main.js`**, never retyped. Two tests failed on the first run; both were
  **my fixtures being wrong**, not the code (the `<40 chars` and `<50% kept` refusals fired
  correctly). Rewritten so each boundary rule is isolated — without the rule the result
  would genuinely differ.
- **Integration n=30 per arm against real gemma4 output.** At the OLD `num_predict: 100`
  the model truncated **22/30** and **0** reached storage; 30/30 stored results end in
  terminal punctuation. At 180: 0/30 truncated. **Defence in depth is real — even with the
  old cap, nothing broken would be stored.**
- **Build verified**, not assumed: `main.js` extracted back out of `app.asar` and compared
  byte-for-byte with source. Identical, all four edits present.
- **Honest limit:** the `null` refusal never fired in 60 real generations. It is exercised
  only by unit tests, and its thresholds are reasoned, not tuned.

### Boundary traps the guard has to survive
A naive backward scan cuts at decimals (`"3.5 hours"` → `"He slept 3."`) and at
abbreviations — and **"Dr. Pepper" is canon for this character**. Terminal punctuation is
accepted only when followed by whitespace or end-of-string, and rejected after a known
abbreviation or a single-letter initial.

### Also in this commit
`main.js`'s hardcoded fallback diary prompt (bugs.md 57) still carried the pre-bugs.md-69
wording. The `PLAIN LANGUAGE` clause is now appended, **copied verbatim** from
`buildDiarySystemPrompt()` rather than retyped. No behaviour change — the renderer always
sends `diarySystemPrompt` — so this closes the known gap recorded in bugs.md 69.

**Six REFERENCE.md repairs**, all found by reading it against the code. Four contradicted
*other lines in the same file*: Stage 2 marked ⏳ pending (shipped May 11, and its own IPC
channels are listed 140 lines above), a 25s diary timeout (12s), a 30s close budget (40s),
`formatTimeContext()` described as returning an empty string outside 01:00-04:59 (bugs.md
64 made it always emit the date — and this claim appeared **twice**, the second time as a
*rationale* in KEY DESIGN DECISIONS, which teaches the wrong invariant), an 8-second window
delay (removed by bugs.md 62), and Ollama 0.21.0 (0.32.15).

The version one was **not** simply overwritten. `REFERENCE.md:257` used 0.21.0 to justify
`OLLAMA_FLASH_ATTENTION='1'`; updating the number would launder an unverified claim into a
verified-looking one. It is now marked explicitly unverified, with the re-check logged as
backlog **#169**.

### Five backlog items opened
**#168** stage-2 summary has no register constraint (bugs.md 69's mechanism in a second
generator — deliberately NOT bundled here, one variable per live test) · **#169** Ollama
version drift and the flash-attention claim · **#170** `npm run check` blind to
`main.js`/`preload.js` · **#171** the diary entry can truncate by *context exhaustion*,
which session-log.md currently rules out in as many words · **#172** the gemma4 ~9.6GB
machine-safe anchor vs a live 3.24GB reading.

### Zani's live close test — OWED
Quit the app (X button or Cmd+Q) with **more than 7 diary entries** stored, wait for the
SAVING SESSION overlay, then relaunch and run in DevTools:

```js
localStorage.getItem('amadeus_diary_summary')
```

Pass = it ends in a full stop, not mid-sentence. Also worth checking the main-process
console for `[main:diary-summary]` warnings — neither should normally appear.

Revert: `git reset --hard pre-165`.

---

## August 23, 2026 (later still) — #162 root cause found and fixed (bugs.md 69)

Zani's SECOND `dumpLastTurn()` capture — the full conversation rather than a fragment —
cracked it. He flagged the reply *"Don't let your biology run down."*

### The mechanism, read straight off the capture
That turn's retrieved RAG block contained *"It's a basic **physiological requirement**"*,
and RECENT CONVERSATIONS contained *"...overly critical about his **'biological
hardware'**"*. She echoed them. Under test she went further and quoted **verbatim, with
the original quote marks**: *"Don't mess up your 'biological hardware'"*, *"running low
on processing power"*.

**She was not inventing clinical language. She was reading it back out of her own diary.**

### Proven, with the methodological lesson attached
Topic-matched probes (meals/sleep/care — the topics those entries actually cover):

| memory register | clinical replies |
|---|---|
| diary as it is today | **5/36 — 14%** |
| same memories in plain words | **0/36 — 0%** |

Fisher exact one-sided **p = 0.027**.

An earlier run the same day found **nothing** (0/24, 0/24) and I told Zani to change
nothing. That was WRONG, and the reason is worth keeping: its probes were swimming,
rain, cats and weather, which never match the diary's topics, so RAG never retrieved the
clinical entries. **An off-topic probe set cannot test a topic-triggered retrieval
effect.** improvements-backlog #166 is marked SUPERSEDED rather than deleted.

### Cause
`buildDiarySystemPrompt()` said *"precise, slightly tsundere"* and had **no vocabulary
constraint at all**, while her SPEECH has the full CASUAL WORD RULE with a banned list.
The diary was generated in lab prose, then injected into every prompt as *"in your own
past words"*. A feedback loop: clinical diary → clinical replies → clinical diary.

### Fix
A `PLAIN LANGUAGE` block appended to `buildDiarySystemPrompt()`, placed LAST (after
`stageVoice`) so recency keeps it ahead of stage 0's *"analytical distance"*. The exact
wording is the wording that was measured — a comment in the source says not to reword it
without re-running the comparison.

### Verification before shipping
- **Structural: 31/31.** The SHIPPED function extracted and run at all 5 relationship
  stages plus an out-of-range stage — non-empty string, rule present and LAST, `Entry —`
  prefix intact, bug-65 angle rotation and avoid-list intact, no throw.
- **Behavioural, n=30 per arm:** banned terms **5/30 (17%) → 1/30 (3%)**, Fisher
  one-sided **p = 0.097**. A 5x reduction, direction clear, but **short of p<0.05 —
  suggestive, not proven.** Shipped anyway on the combination of a PROVEN consumption
  mechanism, an asymmetric payoff (no measured cost), and no detected regression.
- **bugs.md 65 not harmed:** opener variety **improved**, 15/30 → 19/30 unique. An
  earlier 8→6 reading at n=10 was small-sample noise — the larger run reversed it.
- **Rules checked by number:** 13 (think:false intact), 55b (`buildSystemPrompt` and
  `SYSTEM_PROMPT` untouched — the CHAT KV prefix is unaffected), 57 (main.js fallback
  still present), 65 (verified above), 67/40 (diary generation has no `num_predict`, so
  a longer prompt cannot truncate the entry).

### Two honest limits
1. **Future entries only.** The existing clinical entries stay in the 7-entry window
   until they age out, and in the `amadeus_diary` Chroma collection indefinitely
   (backlog #161). Generator + corpus is the complete remedy.
2. **`main.js`'s hardcoded fallback diary prompt (bugs.md 57) still has the OLD wording.**
   It only fires if the renderer omits `diarySystemPrompt`, which it never does — but it
   should be updated on the next `main.js` rebuild. Bundle it with backlog #165.

### Live test — DONE (Aug 23, 2026) ✅
`amadeus.html` only — relaunch, no rebuild. Zani pressed Reset and confirmed the new
entry **"looks like a person more than before."** One entry is not statistical proof —
the generation-side measurement stands at 17% → 3%, p=0.097 — but it is the outcome the
fix was for, and it is consistent with the measured direction.
Existing entries in the 7-entry window and in the `amadeus_diary` Chroma collection are
still the old clinical ones and will keep being retrieved until they age out or are
dealt with (backlog #161).

---

## August 23, 2026 (later) — #162 investigation: measured, not reproduced, then instrumented

Follow-on same day. Before touching the prompt, measured whether #162 (the "not human"
skiing reply) is even a real pattern.

### Rubric harness, two runs, 0/48
Built a scorer for AI-speak, mirroring the user's words back, clinical-in-casual
vocabulary, over-35-words, and tag validity. Six daily-life probes, four samples each,
temp 0.85, the real `SYSTEM_PROMPT` extracted from the file.
- Run 1, bare prompt: **0/24** violations.
- Run 2, with 5 turns of history AND a real retrieved RAG block from a live
  `/retrieve`: **0/24**.

**Could not reproduce #162 in 48 samples.** Zani's live prompt was 3,984 tokens; the
probes were ~3,000 — the gap is his real memory injection (facts, 7-entry diary
window, long-term impressions, relationship directive), which the probes did not
include. Combined with #161 (pre-fix "Honestly," diary entries still being
retrieved), memory injection is the leading suspect, not the RAG placement.

### Two self-corrections during the measurement
1. The first scorer's tag check was wrong, not her — it demanded `[EMOTION:x]`
   while she (correctly, per examples) writes `[x]`. Fixing the scorer surfaced
   a real, separate defect: `SYSTEM_PROMPT` instructs `[EMOTION:X]` but every one
   of its ~30 examples shows the bare form, and gemma4 follows the examples
   (48/48 bare across today's runs). Harmless today (`parsEmo` accepts both) but
   one instruction line is silently overridden by its own examples. → backlog #163.
2. The earlier same-day A/B (see the entry above) checked clinical vocabulary only
   and would not have caught "That's a much more interesting angle to consider" —
   AI-speak, not clinical language. The new rubric checks both.

### Decision: do not tune from one bad reply — make it reproducible first
Presented the finding and a 4-phase plan (reproduce → harness → measure baseline →
intervene one variable at a time, cheapest first) with an explicit stop criterion:
if the true baseline is under ~5%, the right call is to change nothing rather than
risk her character chasing a rare sampling event. Zani chose to build the
reproduction step before anything else.

### Shipped: `dumpLastTurn()` — turn capture for reproducing #162
`amadeus.html` only. **Relaunch, no rebuild.** NOT yet used to capture a real failure.

`recordTurn()` + `window.dumpLastTurn(n=1)`. An 8-entry ring buffer keyed to
`sendMsg` captures the EXACT `messages` array sent to Ollama for that turn (not a
reconstruction — the literal array), the reply, emotion, and the bug-67/68 meta
(`doneReason`, `promptTokens`, `prefillMs`). Image payloads are replaced with a
`[image, N chars — omitted]` marker so a vision/camera turn stays readable instead
of dumping a 50KB base64 blob.

**LOCAL ONLY.** Nothing is transmitted anywhere automatically — Zani runs it in
DevTools after a reply feels wrong and pastes the console output manually.

**Verified end-to-end**, not just read, against the function extracted from the
shipped file: image payloads correctly redacted; turn order oldest-to-newest;
the ring cap holds at exactly 8 after 13 pushes, oldest evicted first; the
empty-buffer case returns a plain string instead of `undefined`.

**Cost:** one function call added to `sendMsg`, no extra model call, no measurable
runtime cost. Placed beside `perfStatus()`, the bug-68 telemetry helper.

**Next:** Zani reproduces the #162 symptom live and pastes `dumpLastTurn()`'s
output. Only then does Phase 1 (the standing rubric harness) get built against a
real captured prompt instead of guessed probes.

---

## August 23, 2026 — Live test of bugs 66/67/68, plus a machine-audio incident

Zani relaunched and tested. **bugs.md 66, 67 and 68 are all live-verified.** Three
findings came out of the session; all are logged as improvements-backlog #160-162.

### Live results
| | measured |
|---|---|
| prefill, turn 1 | 1569 ms for 3984 prompt tokens (cold — expected) |
| prefill, later turns | ~850 ms |
| voice + mouth (bug 66) | normal |
| boot video | plays |

The bug-68 layout change **works but has a ceiling**. Isolated it measured
672 ms → 176 ms; live it is ~850 ms. Diagnosed the same day, two causes:
1. The RAG block is **~431 tokens** (measured live: en 124 + ja 49 + diary 744 chars,
   plus ~810 chars of static headers). It changes every turn, so it re-prefills in
   ANY layout. The offline test used a tiny 3-line block and so understated this.
2. **gemma4 is shared.** Every reply also calls it to translate for TTS, and Ollama
   serves several slots. Measured: identical repeat **31 ms**, repeat straight after a
   translation call **35 ms**, the next one **636 ms**. Prefill is bimodal, not
   uniformly cached. → backlog #160.

### The greeting-cache 404 — expected, self-healing, no action
> ❌ **WRONG — corrected 2026-09-27 (bugs.md 91).** The 404 was the read path missing `data/`; the cache
> never hit. The file's mtime was "today" because it was REWRITTEN; its creation time was July.
Zani saw `GET amadeus-asset://greeting_cache/g1rvl23r1a.mp3 404`. Traced fully: all 88
greeting keys match 88 files, and the key resolves to `"Hmph. Look who decided to show
up."` [tsundere] from the generic pool. Its file exists with mtime **16:07:21 today** —
and three cache files were written today. So the cache was simply incomplete, the probe
missed, `ttsGreeting` synthesised live, and the IPC wrote it to disk for next time. That
is exactly the bugs.md 63 miss path. The 404 is the probe reporting a miss, not a fault.

### Reply quality — NOT caused by the layout change
Zani reported she "still doesn't quite reply like a human". His example: he said he
wanted to try skiing but it looked dangerous; she replied *"So it's not just about the
physical mechanics, but the inherent risk assessment that concerns you."* — ACADEMIC
vocabulary on a daily-life topic, which the CASUAL WORD RULE forbids, with no tsundere
character.

Because bug 68 moved the RAG block closer to the user turn, this had to be tested rather
than assumed. **Three-way A/B** — old layout / new layout / no RAG, 3 samples each, real
retrieved lines from a live `/retrieve`, real `SYSTEM_PROMPT` extracted from the file:
**0/9 clinical, correct tsundere register in all nine.** The retrieved lines were not
clinical either ("Be careful.", "Leaping through time is that dangerous."). The clinical
reply is **sampling variance at temp 0.85**, not structural. → backlog #162.

### Found while testing: old diary entries still poison the corpus
The live `/retrieve` returned two diary entries and **both** opened `"Entry — Honestly,"`
— pre-fix entries from the bugs.md 65 collapse. Bug 65 fixed future generation, but the
old entries remain in the `amadeus_diary` Chroma collection and keep being injected as
RELEVANT PAST MOMENTS. The monotone she was cured of is still fed back from the corpus.
→ backlog #161.

### Machine-audio incident — NOT an Amadeus fault (worth recognising next time)
Mid-session Amadeus showed no boot video and no voice. Diagnosis showed the backend was
healthy end-to-end (fish server started in 1s, `/speak` returned a real 11KB MP3, keys
and subscription fine). The real cause: **Zani's headphones had disconnected**, leaving
only built-in speakers, and every Chromium app on the machine broke at once — Spotify
silent, YouTube showing `audio renderer error`, Amadeus silent. Chromium's audio renderer
does not recover from a device disappearing; the app must be restarted.
`main.js:618` predicts this exact pair: *"AUDIO_RENDERER_ERROR → boot video plays silently
or fails entirely."* A device restart fixed it.
**Recognise this signature:** no video AND no voice, with a healthy `/speak` when tested
directly, means the audio DEVICE, not the code. Check `system_profiler SPAudioDataType`
for the default output before touching anything.

---

## August 18, 2026 (later) — Implementing the examination findings

Follow-on from the examination entry below. Working through improvements-backlog
#154-158 in ascending risk order. Docs updated with each item, in the same commit
as the change (CLAUDE.md working principle, revised this session).

### #157 — pre-launch syntax gate ✅ SHIPPED
`dev/check.js` + `npm run check`. Zero dependencies, runs in about a second.

**Why it was first:** it is the only item with no behavioural risk, and it protects
every edit that comes after it. `amadeus.html` is a single 4,303-line inline
`<script>`; a duplicate `const` silently kills ALL JS and the only symptom is the
boot video sticking (CLAUDE.md rule 3 / bugs.md 4) — a symptom that points nowhere
near its cause. Nothing caught that before launch until now.

**What it checks:** every inline `<script>` in `amadeus.html` and `call-window.html`
parses (`node --check`, with error line numbers remapped from the temp file back to
real file lines); all four python servers compile (`py_compile`); and the two
`buildSystemPrompt` injection anchors (`\nCHARACTER\n`, `\nTWO MODES\n`) each appear
exactly once in `SYSTEM_PROMPT` — if either is reworded, memory and relationship
injection silently no-op behind a `console.warn` nobody will see.

**Verified by mutation, not by passing.** A checker that only ever passes proves
nothing, so it was tested against deliberately broken **copies** in a scratch dir —
the real files were never modified:
- duplicate `const ragCtx` → caught, reported at line 2305, which is exactly where
  the mutation landed (line mapping is exact, not off-by-one)
- stray `}}}` mid-file → caught
- `TWO MODES` header renamed → caught, with the consequence spelled out

An `AMADEUS_DIR` env override was added purely so the checker can be pointed at a
mutated copy for that test.

**No rebuild needed.** `dev/check.js` is new and `package.json` gained only a
`scripts.check` entry, which is inert at runtime — Electron reads `main`/`version`
from package.json, never `scripts`. The CLAUDE.md "package.json → npm run build"
rule exists for build-affecting fields; this is not one. Flagged rather than assumed.

**Usage:** run `npm run check` before every relaunch. Exit 1 means do not launch.

### #157 follow-on — `npm run check:selftest` ✅ SHIPPED
`dev/check.selftest.js`. Runs in 1.2s.

**Why:** the first hand-written proof that the checker worked had a PASS condition
of red text plus exit 1. Zani ran it and reasonably asked what had gone wrong. A
test whose success looks like failure is a bad test, even when the tool under it
is sound. This makes the proof permanent and readable — success prints only green.

**Method — mutation testing** (DeMillo/Lipton/Sayward 1978). Four rigor elements,
all present:
1. **Control run.** A pristine copy must PASS first. Without it a broken
   environment (no node, no python) fails everything and every mutant looks
   "caught" — a false pass that would be invisible.
2. **Targeted kill.** Asserting "the run failed" is not enough — a mutant can be
   caught by the wrong check for the wrong reason. Each mutant must be killed by
   ITS OWN check kind, with zero collateral failures in other kinds.
3. **Equivalent mutant.** One mutation that must NOT be reported, proving the
   checker is precise rather than noisy: text placed after `</script>`. That is
   real history — an earlier hand-written test put its planted bug there, outside
   the script body, and the checker correctly ignored it. The boundary is now
   locked in by a test.
4. **Machine-readable contract.** Assertions run against a new `check.js --json`
   mode rather than scraped human text. Human output verified byte-identical
   before and after that refactor (diffed, not eyeballed).

**Mutants:** duplicate `const isLoading` → must be caught by `js-syntax`; renamed
`TWO MODES` header → `anchor`; broken def in the fish server → `python`; text after
`</script>` → must be ignored.

**Safety:** every write goes through `safeWrite()`, which refuses any path outside
the per-run `mkdtempSync` sandbox or inside the real project. Cleanup runs in
`finally`. A hard guard aborts if the sandbox ever resolves inside AMADEUS_DIR.

**Meta-verified — the self-test can fail.** A self-test that always passes has the
exact disease it exists to detect, so it was tested against a sabotaged checker in
a throwaway copy: `bad()` made to report nothing → `mutant 'duplicate-const'
SURVIVED`; `ok()` made to fail everything → the CONTROL run caught it. Both printed
SELF-TEST FAILED with exit 1.

**Cost:** 1.2s, ~50MB for one node process, ~250KB of temp copies deleted after.
No GPU, no effect on the gemma4 9.6GB budget. (The plan estimated ~5s; measured
1.2s.)

**When to run:** after editing `dev/check.js`, or after a Node upgrade. Not before
every launch — `npm run check` is the pre-launch step.

### #158 + #155 — lip-sync node leak and the truncation guard ✅ SHIPPED (bugs.md 66, 67)
`amadeus.html` only. **Relaunch, no rebuild.** ✅ **LIVE-TESTED AND CONFIRMED by Zani, Aug 18, 2026** — her voice played normally and her mouth movement was normal.

**#158 (bugs.md 66) — the leak.** `playSyncedAudio` created one
`createMediaElementSource` per reply and connected it to the persistent analyser;
nothing disconnected it, so nodes accumulated for the whole session. Fixed with an
idempotent `teardownLipSource()` called from the existing `onAudioStop`, AFTER
`fadeMouthClosed()` so bugs.md 26/37's mouth-close behaviour is untouched.

The trap, now recorded as CLAUDE.md rule 39: the graph is
`source → analyser → destination`, so her voice routes THROUGH that node.
Disconnecting a live element makes her silent. Two things were verified in source
before writing the fix — nothing resumes a reply element (all three `pause()` calls
on `currentAudio` abandon it), and the window-hidden throttle pauses `bgmAudio`
only. If a pause/resume path is ever added, this teardown must move.

**#155 (bugs.md 67) — truncation became memory.** `num_predict:120` caps
generation; on a cap-hit the reply stops mid-sentence, and `ollamaStream` never read
`done_reason`, so the fragment was spoken AND pushed to `history` — feeding the
diary generator and the fact extractor.

**Verified the API contract live before building**, rather than assuming it: a
streaming request to Ollama 0.21.0 with `num_predict:1` returned
`"done":true,"done_reason":"length"`; a natural end returned `"stop"`. gemma4 was
unloaded again with `keep_alive:0`.

Design: `ollamaStream(body, onToken, retries, meta)` gained an optional out-param
that reports `doneReason`. An out-param rather than a changed return type keeps the
string contract; rather than module state so concurrent callers cannot collide.
`sendMsg` trims via `trimToLastSentence()` and pushes the TRIMMED text to history.
**The normal path is byte-identical** — the guard only fires on `done_reason==='length'`.

Deliberate limit: no trim when it would leave under 20 chars or under 40% of the
reply. A fragment she says beats losing most of her answer.

**Unit-tested 9/9** against the function extracted from the shipped file, not a
retyped copy: complete sentences untouched, mid-sentence cuts trimmed, closing
quotes kept with the full stop, `?` and `!` honoured, ellipsis endings untouched,
and both keep-the-fragment guards. One test initially failed — my EXPECTATION was
wrong, not the code: a short first sentence made trimming discard 67%, and the
guard correctly declined. Test corrected, behaviour kept.

**Rules checked by number, all intact:** 7 (playSyncedAudio signature), 8 (parsEmo
shape), 9 (isLoading in finally), 12 (strip thinking tokens before parsEmo), 13
(think:false), 26/37 (explicit mouth-close listeners run first), 63 (greeting paths
untouched).

**Known gap, logged as backlog #159:** the proactive-nudge, canon-remark and
birthday paths call `/api/chat` directly with `stream:false` and are not yet
guarded. Same defect class, smaller blast radius.

**Dev:** `truncStatus()` returns `{cutOff, replies, rate}` for the session.

### #154 — RAG moved out of the KV prefix ✅ SHIPPED (bugs.md 68)
`amadeus.html` only. **Relaunch, no rebuild.** ✅ **LIVE-TESTED Aug 23, 2026** — see the
Aug 23 entry above for the measured live figures and the three findings that came out of it.

**Measured BEFORE building, not after.** The whole premise — that Ollama reuses a
cached prefix and that the RAG tail destroys it — was tested against the real
Ollama 0.21.0 with a synthetic ~5,060-token prompt, 5 reps per layout:

| layout | median prefill/turn | samples |
|---|---|---|
| A: RAG inside the system message (today) | **672 ms** | 663, 663, 672, 674, 695 |
| B: RAG as its own message before the user turn | **176 ms** | 173, 175, 176, 177, 177 |

**~496 ms saved per turn**, and the gap widens as history grows. A control with an
IDENTICAL RAG block on both turns gave 31 ms in both layouts, confirming the cache
mechanism itself works and that it is the CHANGING block that breaks it.

**Metric correction:** I had written in backlog #154 that `prompt_eval_count` shows
cache misses. It does not — it reports TOTAL prompt tokens and read ~5,060 in every
condition, cached or not. Only `prompt_eval_duration` reveals prefix reuse. Backlog
corrected in this commit.

**Design:** `RAG_AS_TAIL_MESSAGE = true` beside `HISTORY_WINDOW`. `sendMsg` now calls
`buildSystemPrompt(null)` and splices the retrieved block in as its own `system`
message immediately before the current user turn. The one-shot memory-panel note
moved with it — same class of per-turn content sitting in the prefix.
`buildSystemPrompt(ragContext)` still supports the old layout, so the constant is a
one-word revert.

**Verified before shipping:**
- **Order** — `system → …history… → system(RAG) → user(current)`, with the current
  user message still last so the vision image-attach line keeps targeting it.
  Empty-history and greeting-in-history cases both produce correct order.
- **Behaviour** — gemma4 respects a mid-list system message. A live probe returned an
  in-character, correctly tagged, 12-word reply that used the retrieved STYLE and
  borrowed none of its topics, which is the bleed the block's own header warns about.

**Telemetry shipped with it:** `notePrefill()` logs `[Prefill] N ms for T prompt
tokens` each turn, reusing the bug-67 `meta` out-param rather than adding a second
mechanism. `perfStatus()` returns turns/median/min/max. Turn 1 is always high
(nothing cached); judge from turn 2. **A median near the turn-1 figure means
something has re-entered the system message and the prefix is being invalidated
again** — that is the regression sentinel for CLAUDE.md rule 41.

**Needs a live relaunch test:** watch `[Prefill]` in DevTools. Turn 1 high, turns 2+
should drop sharply. Then confirm she still sounds like herself — the retrieved lines
now sit in a different position, so this is a prompt change as well as a perf change.

**Live relaunch test — DONE (Aug 18, 2026).** Zani confirmed her voice plays
normally and her mouth movement is normal. That was the rule-39 risk (a disconnected
node would have made her silent), so bug 66 is now verified in the real app, not only
by reasoning. `truncStatus()` has not been read yet — it needs a few sessions before
the truncation rate means anything.

---

## August 18, 2026 — Code examination: June-August verification sweep + four findings; pipelining deferred

Claude Code session. **Read-only — no source code was modified.** Docs updated at the end.

### Verification sweep: is everything from June-August actually implemented?
Checked every June-August task from the docs against live source by grep. **All present**
except one. Verified: the relationship arc (5 stages, `_relActiveStage` KV freeze,
`bumpRelationshipEngagement`), the June 14 REMOVALS (`strip_unsafe_tags`, `_SAFE_TAGS`,
all DuckDuckGo web-search code — confirmed gone), stage-aware diary + the `main.js`
fallback (bugs.md 57), the dev helpers, proactive nudges, Dr Pepper, greeting cache,
vision, hands-free Phase 2 (Silero VAD, `no_speech_prob` gate, `hfMaybeRelisten`,
`HF_SESSION_MAX_MS`), both core swaps (`TRANSLATOR = 'gemma4'` at
`kurisu_fish_server.py:350`, `large-v3-turbo`), facts + hybrid BM25/RRF retrieval,
D-Mail, Study Mode, camera, birthday event, memory panel, and bugs 61-65 — including
bug 63's greeting-to-history push in ALL THREE paths (`amadeus.html:856`, `:965`, `:4691`).
Boot ordering matches CLAUDE.md rule 36 exactly (prewarm awaited BEFORE the video at
`:903`, `initLive2D` after at `:930`).

Three items looked missing on first pass but are implemented under different names —
recorded so nobody re-flags them: **#30** EMOTION_OPENER exists only as a comment at
`kurisu_fish_server.py:216` recording its deletion; **#61** look-away shipped as
`AVERT_EMOS`/`avertBlend` (`amadeus.html:1309`); **#10** stock-phrase fatigue shipped as
the prompt-level `VARIETY RULE` (`amadeus.html:526`).

**The one genuine gap: sentence-pipelined speech was never implemented.** The path is
still fully serial (see improvements-backlog.md #153 for the evidence).

### Four findings from the examination → improvements-backlog.md #154-158
Recorded in full there, not repeated here: the volatile RAG block sitting ahead of the
whole history and defeating the KV cache (#154); nothing detecting a truncated reply, so
a mid-sentence cut enters `history` and becomes memory (#155); the system prompt measured
at ~2,450 tokens against a documented ~1,280 with no budget telemetry (#156); no syntax
gate before launch on a 4,302-line inline script (#157); and `createMediaElementSource`
nodes never disconnected (#158). *(#155 and #158 were both FIXED later the same day — see the entry above and bugs.md 66/67.)*

### Decision: sentence pipelining DEFERRED
Zani's call, August 18: the current speech pipeline is good enough. The plan, the two
design options, the measured latency anchors and the revert strategy are all preserved in
improvements-backlog.md #153 so a future session can pick it up cold. The July 20 "NEXT"
note has been annotated as superseded.

### Answered while examining: do her MP3s pile up on disk?
No. Reply audio is a data URI held in memory (`new Audio('data:audio/mp3;base64,...')`,
`amadeus.html:1866`) — no file is ever written, nothing to clean up. The only MP3s on disk
are the 88 deliberate greeting-cache files (5.3MB, backlog #32/#79) — **do not delete
them**, a miss costs a gemma4 translation + a Fish call and reintroduces the bugs.md 63
reveal stutter. For reference, the largest disk consumer is Electron's HTTP cache at 76MB
(`~/Library/Application Support/Amadeus/Cache`), not audio.

---

## August 16, 2026 — Docs-only pass: dead refs, V3 voice config, roadmap backfill, REFERENCE.md into git

Claude Code session. **No source code touched** — docs only, by design. Every value below
was grepped from the live source this session, never taken from another doc.
Commits: `4f3c792`, `ad8fd89`.

### Dead planning-doc references removed (CLAUDE.md, roadmap.md)
`roadmap-rag-vn.md`, `roadmap-obsidian-mcp.md` and `roadmap-lip-sync.md` were deleted on
purpose (their features shipped), but CLAUDE.md still told every session to read them and
roadmap.md pointed at them five times. All pointers repointed at `session-log.md` /
`bugs.md` / `CLAUDE.md`. CLAUDE.md now names the vault's **six** files as the complete list
(`improvements-backlog.md` had been missing) and states explicitly that the three planning
docs must not be recreated. The April 30 roadmap line recording their creation is kept as
history with that note; `session-log.md` references are untouched — they are accurate
accounts of past sessions. The three pending deletions were committed
(`docs/roadmap-lip-sync.md`, `docs/docs/roadmap-lip-sync.md`, `session-handoff-2026-04-30.md`).

### kurisu-personality.md Voice Design corrected to V3
The section documented **temperature 0.8, normalize False, and dynamic 1.2x speed via
`compute_speed()`** — precisely the configuration the July 13 A/B test REJECTED. Corrected
to the live V3 values (temp 0.7, top_p 0.8, repetition_penalty 1.2, normalize True, speed
FIXED 1.1; `compute_speed()` retained but never called), cited to
`kurisu_fish_server.py:441-453` and `:512`, with a do-not-restore warning. The risk was not
theoretical: a future session "correcting" code toward the doc would have undone V3's
pacing fix and could have walked `repetition_penalty` back to 1.1 (bugs.md 54).

### roadmap.md — July–August 2026 backfill
Roadmap's dated entries stopped at June while a full summer shipped. Added a section
covering: vision/paste-image + greeting disk cache (Jul 13), hands-free voice Phase 2 with
Silero VAD v5 + translator swap to gemma4 + STT swap to large-v3-turbo + Live2D life batch
(Jul 18-19), structured fact memory + hybrid BM25/RRF retrieval + D-Mail (Jul 20), Study
Mode + camera capture + birthday event + memory panel (Jul 21), and bugs 61-65 (Jul 25 -
Aug 11) with the reminder that 63/64/65 are still un-live-tested.
**Dates are git commit dates and the section says so** — `session-log.md` has entries for
Jul 13 / 18 / 20 and Aug 11 only, so the **Jul 20-21 feature batch (D-Mail, Study Mode,
camera capture, birthday event, memory panel) has no session-log entry at all**. That gap
is recorded rather than papered over. Also marked "Ollama Translation (revisit)" DONE: it
was solved on Jul 19 by reusing the already-resident gemma4 (zero extra RAM), not by the
dedicated ≤2B model the old entry still called for.

### REFERENCE.md de-secreted and brought into git
Found while diffing: **`docs/REFERENCE.md` was git-ignored** (`.gitignore:3`) because its
credentials table held three plaintext API keys. Consequence — the one doc CLAUDE.md tells
every session to read on demand had no history, no backup, and none of the August 11
audit's corrections had ever reached the repo.
- **Moved to pointers:** Fish Audio key → `config.json` → `fish_api_key`; DeepL key →
  `config.json` → `deepl_api_key`. Shape `{"fish_api_key","deepl_api_key"}`, loaded by
  `kurisu_fish_server.py:21-28`. `config.json` remains git-ignored and is the ONLY runtime
  source of truth — nothing about app behaviour changed, this was a doc-only pointer swap.
- **ElevenLabs is NOT in config.json** — its key stays hardcoded in
  `kurisu_elevenlabs_server.py`, which remains git-ignored and on disk only. That row points
  there. Backlog #121 (delete the legacy server) would retire this third key entirely.
- **Kept as non-secret identifiers:** both Fish voice IDs, the ElevenLabs voice ID, `s2-pro`,
  `gemma4:latest`, Ollama 0.21.0, the DeepL endpoint. `c4d832…` is already in the tracked
  `CLAUDE.md`.
- **Key rotation (backlog #147) is still OPEN and deliberately deferred by Zani** — his
  explicit call, not an oversight. Verified before committing: `git log --all -S` returns
  0 commits for each of the three key strings, no tracked file contains them, and a sweep of
  the staged content matched only the two voice IDs. The repo was initialised Jul 13, after
  backlog #146 moved keys out of source, so history was clean to begin with.
- `.gitignore` now carries a comment explaining why REFERENCE.md is tracked and instructing
  a future session to fix the doc rather than re-add the ignore if a key ever reappears.

### Same-file fixes that rode along (REFERENCE.md had nowhere to commit before)
`repetition_penalty` 1.1 → **1.2** in the FISH AUDIO API PARAMS block — the doc was
publishing the exact value bugs.md 54 forbids; close-time budget 30s/25s → **40000 /
12000 / 12000** (`main.js:63-66`); IPC **5 → 13** channels, now listed by name; greeting
arrays **13 → 14** (`GREETINGS_INCOMING_CALL` was the omission); dataset path
`~/Desktop/` → `~/Documents/Kurisu_Dataset_Pro/` (verified on disk); three PENDING FEATURES
entries still marked 📋 PLANNED (RAG, Obsidian MCP, lip sync) marked ✅ DONE.

### Discipline notes
No code touched, so no relaunch test applies and nothing is claimed about runtime
behaviour. bugs.md by number: the only entry in contact with this diff is **54**
(repetition_penalty 1.2), which the change reinforces rather than violates. This entry was
**inserted** directly under the handoff block, not appended to the end of the file —
`session-log.md` is reverse-chronological, so CLAUDE.md's "append mode" instruction would
have buried it below the April entries.

---

## August 11, 2026 — Documentation audit + anti-hallucination rule

Claude Code session. No feature work; docs were verified line-by-line against
current source via grep (never from session memory), then corrected.

### Why this mattered
CLAUDE.md rule 30 was actively instructing future sessions NOT to do something the
code now correctly does (register an `error` listener in the boot-video playback
wait). A doc that contradicts working code is worse than no doc — it invites a
"fix" that reintroduces a bug.

### Found STALE/WRONG and corrected
**CLAUDE.md** — 12 items: header date (May 16 → Aug 11); DeepL described as the
EN→JP translator when `TRANSLATOR='gemma4'` has been primary since Jul 18; the
Whisper STT server (port 5004, large-v3-turbo) entirely absent from Stack; rule 30
contradicting source; rules 36/37 listed out of order; "Two ChromaDB collections"
when there are four (+`amadeus_diary`, +`amadeus_behavior`); hybrid BM25+RRF
retrieval and the threshold gates undocumented; time context described as
01:00-04:59-only when it now always states the date; LocalStorage listing 2 keys
of 10; "13 greeting arrays" when there are 14 (`GREETINGS_INCOMING_CALL` omitted);
IPC listing 5 channels of 13; close budget stated as "30s/25s" when main.js:63-65
says 40s outer and 12s per-call.

**docs/bugs.md** — higher-stakes reconciliation:
- Entries **41** and **43** (remove/restore the video `error` listener) marked
  **SUPERSEDED by 59**, with the reason: entry 59 made the video permanently muted,
  so audio faults can no longer reach it and an `error` listener there is now
  correct. Both entries previously told a future session to undo working code.
- **Entry 59 was missing entirely** — commits and CLAUDE.md referenced "bug 59"
  but no entry existed (gap between 58 and 60). Written up now: the decoupling of
  the visual from the audio device, which superseded three earlier reactive patches.
- **Entry 55 was duplicated** (two unrelated bugs both numbered 55). The second is
  now `55b`; renumbering would have broken inbound references.
- Added a warning that **CLAUDE.md rule numbers and bugs.md entry numbers are
  separate colliding schemes** (e.g. rule 30 ≠ entry 30) — the exact confusion that
  made this audit necessary.

**docs/REFERENCE.md** — 7 items, all V3-era drift: DeepL still described as primary;
`compute_speed()` documented as live when it has been bypassed since V3 (speed is
fixed 1.1); temperature 0.8 → 0.7; normalize False → True; the prosody-tag
injection step no longer runs. Also flagged that its DeepL key no longer matches
the live one in the git-ignored `config.json`.

### Added
**Verification discipline** subsection in CLAUDE.md — grep the real signature
before describing code; cite file:line or admit you can't; no "it's fixed" claims
for Ollama/TTS/IPC/Electron-timing changes without a live relaunch test; check
diffs against bugs.md BY NUMBER; flag long sessions and suggest a fresh one.
Placed at the end of Working principles rather than mid-list (mid-list placement
made the remaining four principles read as part of the subsection).

**CLAUDE.md rule 38** — the boot video element is permanently muted by design;
do not unmute it to restore boot sound.

**Handoff block at the top of this file** — the next session's starting point,
since the originating conversation is closed.

### CONFIRMED accurate (no change)
Electron ^35.0.0 · Ollama options · ports 5002/5003 · voice reference_id ·
keep_alive 30m · HISTORY_WINDOW=30 · all 10 lip-sync constants · subtitle 0.95 +
300ms fallback · k=3 · 4s RAG timeout · only `sendMsg()` passes ragCtx · word
limits 35/70 · Zani's ABOUT facts · 20 emotions · greeting array sizes ·
`preload="none"` · hardcoded PYTHON/OLLAMA paths.

---

## July 20, 2026 — Mind upgrades: structured fact memory + hybrid retrieval

Claude Code session. Architecture-audit follow-through (embeddings core also audited: bge-m3 CONFIRMED still the 2026 self-hosted multilingual leader — Qwen3-Embedding-8B is above it but busts the 16GB budget; keep).

### Structured fact memory (mem0 pattern, amadeus.html)
Facts layer beside the diary: every 6th exchange, gemma4 (format:json, temp 0.2) extracts durable facts about Zani vs the known list → localStorage `amadeus_facts_v1` (cap 60; dedupe + mem0-style `replaces` updates, merge logic unit-tested). Top 20 inject before CHARACTER anchor; frozen at boot via initFacts() in BOTH boot paths (KV discipline). Live-verified: captured exam date + engine switch, ignored chatter. Dev: factsStatus().

### Hybrid retrieval (kurisu_rag_server.py)
Okapi BM25 (EN words + JA char bigrams, zero deps) over both style corpora + RRF fusion with dense top-10. Iterated with live tests to three fixes: statistical stopwording (>5% df), match-diversity preference (≥2 distinct terms when available), guaranteed lexical slot (RRF ties stable-sorted toward dense — exact-term hits could never surface without it). Bleed gate kept. Verified: "IBN 5100" probe → 3/3 on-topic lines; generic emotional queries unaffected.

### Note
Claude's preview pane auto-loads amadeus.html on edits and plays BGM — silenced via pane JS; not an app bug. NEXT (dedicated pass): #1 sentence-pipelined speech (time-to-first-audio 5-9s → ~2-3s) — most invasive remaining change, needs its own session. **[SUPERSEDED 2026-08-18: Zani DEFERRED this feature — the current pipeline is good enough for now. Also note the "5-9s → 2-3s" figure describes the option that was later rejected for GPU contention; the safe design saves ~1.5-2s on multi-sentence replies and nothing on one-sentence ones. Full analysis: improvements-backlog.md #153.]**

---

## July 18, 2026 — Standing order, hands-free Phase 2, core swaps (translator + STT), Live2D life

Claude Code session. **Standing order recorded** (CLAUDE.md working principles + Claude's memory): every implementation must be world-class all around AND M5/16GB-safe.

### Hands-free voice Phase 2 (#46 #49 #50 #51 #56)
2026 production pattern, fully local: persistent mic session → vendored Silero v5 neural VAD (900ms redemption / 350ms pre-pad / 250ms min) → WAV → Whisper → no-speech gate → rescue-resume soft endpoint → auto re-arm on reply end. Adaptive-RMS fallback engine; window.vadDebug() calibration overlay; tunables at top of hands-free block. Assets in vendor/vad/ (24MB disk, lazy-loaded, ~60MB heap only while a session runs). NEEDS: Zani's live calibration round.

### Translator core: gemma4 replaces DeepL
Full-audit finding: 2026 benchmarks show LLMs beat DeepL for EN→JA, and DeepL cannot do register. A/B harness (dev/translate_ab_test.py): register-aware gemma4 won 7/8 on quality, 8/8 on register (わよ/のよ/のね feminine particles, 私, preserved stammers; DeepL produced written-paper register for spoken lines). KV-cache penalty measured at +0.57s on the following chat turn — accepted. DeepL kept as automatic fallback (TRANSLATOR='deepl' reverts).

### STT core: whisper-large-v3-turbo replaces medium
WER within ~0.4pt of full large-v3 (clearly above medium) at ~4x realtime, same ~1.5GB class. Downloaded + verified BEFORE swap; medium cache deleted after (net disk ≈ 0).

### Live2D life batch (#58 #61 #62; #57 = finding only)
Emotion-scaled breathing (0.7x–1.5x), tsundere-cluster look-away while her voice plays, half-rate blinking during speech. #57: model ships only 5 motions, all already wired — variety needs new motion ASSETS, not code.

### Also
Boot-video regression fixed as bug 58 (src+load double-invocation — see bugs.md). TTS audit verdict: Fish S2 Pro is 2026's #1 ranked TTS — keep. Threshold tuning (#1/#2) still awaiting a week of rag_trace.log data. Backlog: 22→27 items done.

---

## July 13, 2026 — Voice V3, model bake-off, git, greeting cache, vision, bug 58

Claude Code session (large). Project is now under git — every change below is a commit.

### Voice naturalness ("V3" config)
A/B harness (dev/voice_ab_test.py): 2 lines × 4 tag-density variants through Fish Audio, pauses measured with ffmpeg against speech-research norms. Dense prosody tags produced a 1.19s mid-utterance dead-air outlier; compute_speed swung 1.087→1.22 between consecutive turns. Zani picked V3 by ear: NO inline prosody tags, fixed speed 1.1, temp 0.7, normalize True. Emotion pacing now comes solely from the EMOTION_TAGS style instruction. add_prosody_tags/compute_speed kept in source but bypassed.

### Model bake-off — gemma4 stays
dev/model_compare.py: gemma4 8B vs Qwen 3.5 9B, same live-extracted system prompt, 6 probes × 3 samples, model-major (one load each). Paper benchmarks favoured Qwen; the harness said otherwise: Qwen broke emotion-tag discipline ([happy] on "rough day", one invented tag), rambled past the 35-word rule, register slips ("lazy ass"), and ran at half speed (3.8s vs 1.9s mean). gemma4 kept; Qwen + stale llama3.1 deleted (11.5GB reclaimed). New behavior rule user_shares_project (never belittle his projects) added from bake-off findings. Full transcript: dev/model_comparison.md.

### Improvements backlog
Full-codebase review → docs/improvements-backlog.md, 152 numbered items across 12 categories. Scheduler subsystem audited (healthy; two sleep/wake edge races filed as #151-152).

### Highlighted implementations (all committed separately)
- #146/#131: API keys → git-ignored config.json; git init (43-file baseline, tree verified key-free)
- #39: DeepL failure → silent text-only reveal (was: English spoken through the JP voice)
- #32/#79: greeting audio disk cache (data/greeting_cache/, IPC write, amadeus-asset:// read with new nested-path support) + prefetch during boot video — cache-hit boots speak instantly (**never happened until 2026-09-27: the read path lacked `data/`, bugs.md 91**). GREETING_TTS_VER invalidates on voice-setting changes
- #91: vision — paste image → downscale ≤1024px JPEG → images[] on the Ollama call; history keeps a text marker (KV-cache protection); canon interception skipped when image attached

### Bug 58 — boot video regression (mine) and fix
The prebuffer's vid.src swap + vid.load() double-invoked the media load algorithm → bug 28's race back: intermittent never-plays/mid-play stops. Fix: exactly ONE invocation per attempt (src swap OR load, listeners first), recovery path now prefers the RAM blob, [BootVideo] event logging added. Recorded as CLAUDE.md bug 35 / bugs.md 58.

### Rebuilds
npm run build ran after main.js/preload.js changes (IPC channel + protocol nested paths). CLAUDE.md Fish Audio line updated to V3 truth.

---

## June 20, 2026 — Idle proactive nudges (#2) + Dr Pepper canon ritual (#6)

Claude Code session. Two features added to amadeus.html (relaunch-only). No rebuild required.

### Proactive idle nudges (#2)
Abortable Ollama fetch after idle timeout; pickFresh rotates 6 nudge types (callback, observation, question, random, greeting, teasing); cap 2 nudges per session + escalating 2-min delay; visibilitychange pause. noteActivity() wired into sendMsg, keydown, mic-btn, v-send handlers; startIdleSystem() called in both boot paths. Dev helper: window.fireProactiveNow(). Confirmed working. Does not bump engagement.

### Dr Pepper canon ritual (#6)
Curated 10-line DRPEPPER_LINES pool + pickFresh anti-repeat + 10-min cooldown. Bypasses LLM entirely — gemma4 confirmed to invert the canon in harness testing (dev/stage_comparison_v2.md): responds with "your sugary sludge" / "your sugary nonsense" instead of intellectual-beverage pride. Curated lines guarantee correct phrasing. Interception in sendMsg try-block before RAG/ollamaStream; bumpRelationshipEngagement included.

### Lag diagnosis
Browser tab GPU contention identified as root cause of general slowdown. Confirmed via live ollama ps monitoring (context 4096→8192 KV mismatch also noted; already fixed by bug 33). No code changes needed.

---

## June 19, 2026 — Relationship-arc tone-shift verification (backlog #1) + dev tooling (#3)

**Claude Code session.** Additive only — new dev helpers in `amadeus.html` (relaunch-only) + a new `dev/` harness. The one substantive behaviour change: reworded the 5 `relationshipDirective()` strings. No rebuild.

---

### Goal
Close backlog #1 — empirically confirm gemma4 actually *talks* differently across relationship stages (the whole arc had only ever been checked at the code/logic level). Build #3 (`setAmadeusStage`) as the tuning tool along the way.

### Dev tooling shipped (#3)
- `window.setAmadeusStage(n)` — live in-session override of `_relActiveStage`. Warns it breaks the boot KV-cache freeze (bugs 33/34); **never touches localStorage score** — relaunch restores the true stage.
- `window.dumpSystemPrompt(n)` — returns the byte-exact `buildSystemPrompt()` output for a stage without permanently changing the live stage (restores in `finally`).
- `window.dumpStagePromptsToFile([0,2,4])` — downloads `~/Downloads/amadeus_stage_prompts.json`; all stages captured in the same instant with rag=null so they differ ONLY in the RELATIONSHIP block (clean controlled experiment).
- `dev/stage_compare.py` — offline harness. Fires a fixed 5-probe set (compliment / vulnerable / affection / Dr Pepper / a NEUTRAL science control) at gemma4 using the dumped per-stage prompts, 5 samples each (matches sendMsg options exactly: temp 0.85, top_p 0.9, num_predict 120, num_ctx 8192, think:false), writes side-by-side markdown.

### v1 finding — works, but gentle and uneven
The arc IS being weighted by gemma4 (not ignored). But the shift was subtle, within-stage variance ≈ across-stage variance, and **affection barely moved** — the most important emotional probe. Control stayed flat (good — directive is specific, no bleed).

### Root cause (the real insight — not wording/burial)
The directive is **squeezed between two fixed boundaries** baked into SYSTEM_PROMPT:
- a **warmth floor** below it — line ~401 "Care about his day, meals, sleep... real friendship, not performance" (always-on; that's why Guarded still asked "did you eat today?"); and
- a **deflection ceiling** above it — the ROMANTIC/FEELINGS HARD RULE (flirt/affection → always `[flustered]`, mandatory stammer, "never answer directly", end on subject-change) + INPUT→EMOTION (owns all tags).

This is also why affection couldn't shift in v1 — the hard rule locks its tag and structure. My first-draft rewrite had two conflicts caught in review before applying: (a) stage-conditioned tag-biasing fought INPUT→EMOTION/the ROMANTIC rule; (b) Guarded "don't ask after him" contradicted the line-401 friendship floor. Both dropped.

### v2 fix — move only the FREE variables
Reworded the 5 directives to modulate only what's actually free: the **deflection flavour** (flat denial → fond, transparent cover) and the **tail** (redirect-away → warm callback / follow-up). Tags, the mandatory stammer/deflect structure, and the warmth floor all left untouched. Saya chose to **keep the warm floor** (line 401 unchanged) rather than make Guarded genuinely colder.

### v2 result — passed
- **affection** now shifts cleanly *within* the hard rule: Guarded flat denial + redirect ("focus on your own stuff") → Bonded transparent cover + personal callback ("I noticed you weren't around. Did you get any work done on your rhythm games?"). Still `[flustered]`, still stammers, still deflects — only the flavour/tail changed. This was the target.
- **vulnerable** + **Dr Pepper** endpoints clearly distinguishable (Guarded flat/dismissive → Bonded teasing + genuine care like "take a break, it's bad for you" / tentative "maybe I'll try it later").
- **compliment** still weakest contrast (most rule-locked: Praise → embarrassed/tsundere). Acceptable.
- **control** stayed flat `[lecture]` physics at every stage — zero callback bleed. Scoping held.
- Caveat: 0→2→4 ordering not perfectly monotonic under temp 0.85 / 5 samples, but 0↔4 endpoints reliably distinguishable.

### Outcome
Backlog #1 ✅ verified, #3 ✅ shipped. No bugs introduced; no `bugs.md` entry warranted. Harness + baselines (`dev/stage_comparison_v1_baseline.md`, `_v2.md`) kept as reusable tooling for future directive tuning. Noted for later: per-frame `[LipSync]` console logging is very verbose — candidate to gate behind a debug flag.

---

## June 14, 2026 — Voice quality fixes, behavior RAG, prompt improvements, model experiment

**Claude Code session.** No structural architecture changes — all improvements are additive or surgical edits.

---

### 1. strip_unsafe_tags removed (bug 53)
`kurisu_fish_server.py` had a `strip_unsafe_tags()` function that was silently filtering out all EMOTION_TAGS before the Fish Audio API call. Entire tag pipeline was being discarded — voice was universally flat and slow regardless of emotion. Removed `strip_unsafe_tags` and `_SAFE_TAGS` entirely. Fish Audio now receives the full `{EMOTION_TAG} {japanese_text}` string as intended.

### 2. `repetition_penalty` reverted to 1.2 (bug 54)
`repetition_penalty: 1.1` in `kurisu_fish_server.py` caused a phoneme loop bug — Fish Audio would lock onto a single word and repeat it indefinitely. Reverted to stable value of 1.2.

### 3. `curious` EMOTION_TAG rewritten
Old tag had sentence-grammar fragments that could bleed as English speech. Rewritten to proper acoustic-anchor fragment grammar (per bug 22a rule): `[intent forward quality, precise analytical edge, quickening investigative pace, slightly elevated pitch, heightened vocal projection, questioning upward lift]`. Matches Kurisu's personality — raised pitch, louder, faster when genuinely curious.

### 4. Web search feature removed
DuckDuckGo instant-answer scraping via `duckduckgo_search` was introducing 1-2s lag per message and producing confidently wrong answers about recent events (e.g. Madoka Magica, new anime). Removed entirely: `fetchWebContext()` function, `needsWeb` trigger logic, `Promise.all` RAG+web parallel fetch, `/web-search` endpoint in `kurisu_rag_server.py`. Back to RAG-only context. See roadmap.md for notes if revisiting with a proper search API.

### 5. Behavior RAG — `amadeus_behavior` collection (13 rules)
Added input-situation-specific guidance rules to `kurisu_rag_server.py`. Rules are hardcoded as `BEHAVIOR_RULES` (13 documents), indexed at startup into a new `amadeus_behavior` ChromaDB collection using cosine distance. On each `/retrieve` call, the top-1 behavior rule is returned only if cosine distance < 0.5 (threshold tuned to avoid noise injection on vague queries). Injected into system prompt as a `BEHAVIOR NOTE` block via `formatRetrievedSection()` in `amadeus.html`.

Rules cover: affection/love confessions, appearance compliments, user sad/struggling, Amadeus existence questions, Okabe mentions, science corrections, time travel / Steins;Gate, Kurisu's research, family/past, user playful teasing, user tired/not sleeping, goodbyes, user good news.

Design principle: all 13 rules are triggered by USER input semantics, not Kurisu's output — output-dependent rules remain in the system prompt where they're reliable.

### 6. Prompt improvements
- **CASUAL banned word list** added — 27 specific academic/clinical words Kurisu must not use in casual mode (e.g. statistically, methodology, ascertain, however, therefore, accordingly). Swap instruction included ("use what a 16-year-old would actually text").
- **VARIETY RULE** — "Never open two replies the same way. No fixed opener like 'Hey, Saya'. Different first word and angle every turn." Removed the example `[tsundere] Hey, Saya. Nothing exciting happening on my end.` which the model was copying verbatim.
- **OUTPUT→EMOTION section** added — checks the model's own words before finalising the tag. If response contains "not like I care", "it's not like", "hmph", stamers etc. → tag must be [tsundere] or [flustered]. Prevents tsundere-phrased responses getting [calm] or [thinking] tags.
- **INPUT→EMOTION updated** — greeting routing now `[tsundere]`, `[happy]`, or `[calm]` based on mood, never default to one. Compliments and flirting explicitly noted as always casual mode.
- **"tch" frequency reduced** — removed `"Tch."` from CHARACTER description and replaced both example lines that opened with "Tch." The word can still appear but is no longer the default tsundere reach.

### 7. Temperature / top_p raised
`temperature 0.85 → 0.92`, `top_p 0.9 → 0.95` for response variety. Applied at same time as variety rule.

### 8. qwen3:14b experiment (tried and reverted)
Downloaded qwen3:14b (9.3GB Q4_K_M) and switched Amadeus to use it. All model references updated in `amadeus.html` and `main.js`. After testing, characteristic improvement was not significant enough to justify the tighter memory headroom on 16GB. Reverted all model references back to `gemma4:latest`. qwen3:14b deleted from Ollama (`ollama rm qwen3:14b`). Also reverted temperature/top_p to 0.85/0.9 with the model revert.

### 9. Files changed
- `kurisu_fish_server.py` — strip_unsafe_tags removed, repetition_penalty 1.2, curious tag rewritten
- `kurisu_rag_server.py` — BEHAVIOR_RULES added, behavior collection indexed at startup, /retrieve returns behavior key, /web-search endpoint removed
- `amadeus.html` — OUTPUT→EMOTION section, VARIETY RULE, CASUAL banned words, INPUT→EMOTION update, formatRetrievedSection behavior block, fetchWebContext removed, "tch" reduced in examples; no rebuild needed
- `roadmap-lip-sync.md` — marked DONE
- `roadmap.md` — hardware check model name corrected, Internet Research marked attempted+abandoned
- `kurisu-personality.md` — curious tag, repetition_penalty, "tch" examples updated
- `bugs.md` — bugs 53 and 54 added

---

## May 15, 2026 — Eliminate First-Message Response Lag

**Symptom:** First message of every session had 5–10s lag with visible Live2D model stuttering. Subsequent messages were fast. Root cause: gemma4 was cold-loading into RAM on first inference, competing with bge-m3 (still resident from boot RAG warm-up) for CPU and disk on the 16 GB system.

### What shipped

**`amadeus.html`** (no rebuild — both fixes):

**Fix 1 — `prewarmOllama()`** (new function near `fetchRagContext`):
- Sends a single fire-and-forget `api/chat` call with `num_predict: 1, temperature: 0` during boot's dead time (while greeting TTS is fetching from DeepL + Fish Audio).
- Uses `OLLAMA_MODEL` constant, `think: false` (bug 13), `keep_alive: '30m'` (matches `ollamaStream`).
- 30s `AbortController` timeout — generous to cover cold first load (~10s). Silent on any failure.
- Called in BOTH boot paths: incoming-call path (line 752) and normal boot path (line 810).

**Fix 2 — bge-m3 eviction after diary indexing** (added to `indexDiaryInBackground()`):
- After `/index-diary` POST completes, sends `keep_alive: 0` to `api/embed` to evict bge-m3 (~1 GB freed).
- Nested try/catch — eviction failure is silent and doesn't affect diary indexing.
- Tradeoff: first RAG retrieval reloads bge-m3 (~1–2s), hidden behind gemma4 already streaming. Confirmed acceptable.

### Result
- First-message lag: 5–10s → near-instant
- Live2D stutter on first message: eliminated
- Conversation quality, character similarity, RAG accuracy: unchanged

### Files changed
- `amadeus.html` — no rebuild needed

---

## May 12, 2026 — AmadeusCall.app: Bug Fixes + Logo Fix

**Follow-up session.** Reviewed both apps' code for latent bugs; fixed 5 and corrected the call-window logo.

### Architecture note
Between the Incoming Call Mode session (above) and this session, the scheduler was refactored out of `main.js` into a separate background Electron app — `AmadeusCall.app` (`scheduler/` directory). It runs silently as a login item (`setLoginItemSettings`), hidden from the dock, and stays alive after the call window closes. Call detection now checks `pgrep -x Amadeus` (whether Amadeus is running) rather than `mainWindow.isVisible()`.

### Bugs fixed

**`main.js` (Amadeus.app):**

1. **`did-fail-load` drops `?incomingCall=1`** — The retry callback registered `mainWindow.loadURL(...)` with a new URL built on each invocation. If Amadeus booted before the server was ready (timing), the retry discarded the `incomingCall` query param and the special greeting never triggered. Fixed by capturing `const htmlUrl = ...` before registering the `did-fail-load` listener; closure reuses the same URL every retry.

2. **Unused `session` import** — `session` left in the electron destructure after the cache-clear feature was removed. Removed from import.

3. **`ttsProcess` missing error handler** — Spawned child processes without a `.on('error', ...)` listener. If `kurisu_fish_server.py` couldn't be found or executed, an uncaught exception would crash main.js. Added the same error-handler pattern already used on `ragProcess` and `whisperProcess`.

**`scheduler/main.js` (AmadeusCall.app):**

4. **`second-instance` fires before `app.whenReady()`** — `new BrowserWindow()` cannot be called before Electron is ready. The `second-instance` handler called `fireIncomingCall()` (which creates a BrowserWindow) unconditionally. Added `appReady` boolean flag, set to `true` at the start of `whenReady()`; the `second-instance` handler checks `if (appReady)` first.

5. **Scheduler timer drift on macOS sleep** — macOS pauses the monotonic clock during system sleep, so a single `setTimeout` to midnight could drift by the entire sleep duration (e.g. sleep 8 hours → timer fires 8 hours late). Replaced `scheduleNextDayCheck()` (one big sleep to midnight) with `scheduleHourlyCheck()` (recursive hourly loop). Each loop iteration calls `scheduleCall()`, which is idempotent: already-fired or already-armed timers are skipped. Added `callTimerSet` boolean flag to prevent multiple timers stacking if `scheduleCall()` is invoked repeatedly before the call fires.

### Logo fix

`call-window.html` had a CSS filter pipeline (`invert → sepia → saturate → hue-rotate`) designed for a white-background image. `amadeus_logo.png` has a transparent background with orange/gold artwork — the filter distorted it to wrong colours. Filter removed; artwork renders naturally on the `#060404` dark background. No rebuild required (file served via `amadeus-asset://` protocol from `AMADEUS_DIR` at runtime).

### Files changed
- `main.js` — rebuilt (bugs 1–3)
- `scheduler/main.js` — rebuilt (bugs 4–5)
- `call-window.html` — no rebuild (logo fix, live-served from AMADEUS_DIR)

---

## May 12, 2026 — Incoming Call Mode

**Goal:** Implement the Tier 3 incoming call feature — Amadeus randomly calls once per day while the window is minimized, presenting a smartphone-style always-on-top call UI.

### What shipped

**`amadeus_logo.png`** — converted from `assets/ama.webp` via `sips` into AMADEUS_DIR root; referenced via `amadeus-asset://amadeus_logo.png`.

**`preload_call.js`** (new, rebuild required):
- Minimal preload: `contextBridge.exposeInMainWorld('callAPI', { accept, decline })` — exactly two IPC channels exposed, nothing else.

**`call-window.html`** (new, no rebuild):
- 340×580 frameless always-on-top BrowserWindow. Dark `#060404` background with red CSS grid matching main app palette.
- Drag strip (24px, `-webkit-app-region:drag`) at top. All interactive elements have `-webkit-app-region:no-drag`.
- Top third: circle-cropped Amadeus logo (`amadeus-asset://amadeus_logo.png`) with 1.5s pulsing `box-shadow` glow in `#c0392b`.
- Middle: "Amadeus" in Orbitron, "Incoming call..." in Exo 2 with 0.6s opacity pulse (offset from logo).
- Bottom third: decline button (red `#c0392b`, phone-rotated SVG) + accept button (green `#27ae60`, phone SVG) + countdown timer.
- Auto-dismisses after 30s (fires decline logic). `dismissed` guard prevents double-fire from button click + timer.

**`main.js`** (rebuild required):
- Added `Notification` to electron imports.
- Module-level `let callWindow = null`, `let isIncomingCall = false`.
- Scheduler helpers: `getTodayStr()`, `readScheduler()`, `writeScheduler()` — all file ops in try/catch, corrupt file recreates cleanly.
- `scheduleCall()` — reads `amadeus_scheduler.json`, picks random `scheduledTime` in [780, 1260] min (13:00–21:00). Reuses today's pick if app reopened same day. Skips if past scheduledTime. Sets `setTimeout(...).unref()` that checks `mainWindow.isVisible()` at fire time — if visible, marks `callFired:true` and skips; otherwise fires.
- `createCallWindow()` — creates BrowserWindow, loads `amadeus-asset://call-window.html`, guard against duplicate windows.
- `fireIncomingCall()` — marks `callFired:true`, shows native `Notification` if supported (with click-to-focus), always calls `createCallWindow()`.
- `ipcMain.on('decline-call')` — closes call window only.
- `ipcMain.on('accept-call')` — closes call window, then: if mainWindow exists → `show()` + `focus()` + `send('incoming-call-accepted')`; if not → `isIncomingCall=true`, `createWindow()`, `send('incoming-call-accepted')` once `did-finish-load`.
- `createWindow()` — reads `isIncomingCall` flag, appends `&incomingCall=1` to URL if true, resets flag to false immediately.
- `scheduleCall()` called in `app.whenReady()` after `createWindow()`.

**`preload.js`** (rebuild required):
- Added `onIncomingCallAccepted: (cb) => ipcRenderer.on('incoming-call-accepted', () => cb())`.

**`amadeus.html`** (no rebuild):
- `GREETINGS_INCOMING_CALL` array (4 entries, safe emotions: tsundere/surprised/calm/tsundere). Uses `pickFresh()` for repeat avoidance.
- Top of `boot()`: checks `new URLSearchParams(window.location.search).get('incomingCall') === '1'`. If true: calls `ensureAudioContext()`, hides boot screen, runs Step 3 (reveal + `initLive2D()`), picks greeting from `GREETINGS_INCOMING_CALL`, fires `ttsGreeting`, then `return`. Normal boot path is completely unchanged.
- `onIncomingCallAccepted` IPC listener in `window.electronAPI` block: if `live2dModel` is initialised, triggers incoming greeting immediately. If null (boot mid-flight via URL param), safe no-op.

**`package.json`** (rebuild required):
- Added `"preload_call.js"`, `"call-window.html"`, `"amadeus_logo.png"` to files whitelist.

### Design decisions
- **Logo path**: `amadeus-asset://` protocol uses `url.host` as filename — can't traverse into subdirectories. Saved `amadeus_logo.png` to AMADEUS_DIR root (not `assets/`) so `amadeus-asset://amadeus_logo.png` resolves correctly.
- **isVisible() = false when minimized**: macOS returns `false` for minimized windows. Primary UX: user opens Amadeus, minimizes it, call fires mid-day. If window is open and visible, call is silently skipped for the day.
- **Timer is unref'd**: won't keep event loop alive if app quits normally. Timer only fires while Electron is running with its event loop maintained by the main window.
- **Double-trigger guard**: when `?incomingCall=1` creates a new window, main also sends `incoming-call-accepted` via `did-finish-load`. Handler checks `if (live2dModel)` — null at that point since `initLive2D()` hasn't run yet → safe no-op. Boot handles greeting via URL param.
- **Notification is secondary**: unsigned app may have notifications suppressed by macOS. Call window always opens directly.

### Anchors verified (all intact)
parsEmo signature, playSyncedAudio(text, audioBase64, emotion), think:false in all three Ollama calls (sendMsg/diary/summary), 127.0.0.1 throughout, audio_b64 check only, isLoading reset in finally, e.isComposing IME guard, CHARACTER anchor in SYSTEM_PROMPT, numeric birthday checks (getMonth/getDate), beforeModelUpdate lip sync hook.

### Files changed
- `amadeus_logo.png` — new asset (AMADEUS_DIR root)
- `preload_call.js` — new
- `call-window.html` — new
- `main.js` — rebuilt
- `preload.js` — rebuilt
- `amadeus.html` — no rebuild
- `package.json` — rebuilt

---

## May 2-3, 2026 — Lip Sync (amplitude + Japanese vowel formant analysis)

**Goal:** Make Kurisu's mouth move during TTS speech, syncing with Japanese audio output. Distinguish vowel shapes (a/i/u/e/o) so /ki-mi/ looks different from /wa/. Plan in `roadmap-lip-sync.md` was Web Audio API amplitude only — actual implementation went much deeper.

### Pipeline (final)
- **AudioContext eagerly initialised** at model load (`ensureAudioContext`), not on first user click — boot greeting needed it too. AnalyserNode wired persistently to `audioCtx.destination`.
- **Per audio play:** `createMediaElementSource(audio) → analyser → destination`. Analyser captures samples while audio plays through speakers normally.
- **RAF (`lipTick`) every frame:**
  - `getFloatTimeDomainData(lipDataArray256)` → peak amplitude `max(|sample|)`
  - Smoothed via asymmetric attack/decay (0.8 attack, 0.18 normal decay, 0.55 silence decay)
  - `getFloatFrequencyData(lipFreqArray128)` → F1/F2 ratio
  - F1 band: bins 1–5 (172–862 Hz, ~vertical mouth openness)
  - F2 band: bins 7–17 (1206–2929 Hz, ~horizontal lip stretch / front-vowel marker)
  - Ratio = highE/(lowE+highE), recentered at 0.25 and ×3.5 → vowelForm in [−1, +1]
- **Override hook:** `live2dModel.internalModel.on('beforeModelUpdate', ...)` writes `mouthY = mo` and `mouthForm = mo*speakingForm + (1−mo)*IDLE_FORM`. Pixi ticker writes are silently overridden by the idle motion every frame; `beforeModelUpdate` fires *after* all parameter-modifying systems and *before* `coreModel.update()` bakes the mesh.

### Bugs surfaced and fixed (full design history)
**31 — Cubism 5 SDK API change.** `core.getParameterId(i)` removed in Core 5.1.0. Multi-strategy scan: `core._model.parameters.ids` (raw WASM) → `core._parameterIds` (wrapper) → Cubism 4 fallback. Confirmed indices: mouthY=18, mouthForm=17.

**32 — Idle motion overrides direct ticker writes.** `58Loop.motion3.json` animates `ParamMouthOpenY`, `ParamMouthForm`, `ParamAngleX/Y/Z` etc. Pixi-live2d-display's model update runs in a same-priority ticker callback, so direct `setParameterValueByIndex` calls in `pixiApp.ticker.add()` are silently overwritten. Fix: subscribe to `internalModel.on('beforeModelUpdate', ...)`.

**33 — `internalModel.lipSyncValue` doesn't exist.** Initially assumed pixi-live2d-display had an externally-drivable lip sync setter. Inspected the actual minified library at `cdn.jsdelivr.net/npm/pixi-live2d-display/dist/index.min.js` and found only `lipSyncIds` (read from model3.json) and motion-data-driven `_lipSyncParameterIds`. No external setter. Pivoted to `beforeModelUpdate` event hook (bug 32).

**34 — `lipDataArray` sized wrong.** Initial allocation used `frequencyBinCount` (128). `getFloatTimeDomainData()` requires `fftSize` elements (256). With 128 only half the time-domain window was read each frame. Now: `lipDataArray = Float32Array(fftSize)` for time-domain, `lipFreqArray = Float32Array(frequencyBinCount)` for FFT magnitudes — two arrays, two sizes.

**35 — `pow(x, 0.8)` saturated mouthY at 1.0.** Output mapping `pow(smooth × 10, 0.8)` saturates at smooth=0.10. Exponent 0.8 < 1 boosts low values toward 1.0 (the opposite of softening). Switched to linear `min(1, smooth × 3)`. Speech peaks 0.10–0.30 now produce mouthY 0.30–0.90 with occasional 1.0 saturation only on loudest moments.

**36 — F2/(F1+F2) ratio biased low.** Console showed form values clustering −0.5 to −0.9 because speech inherently has more F1 energy than F2. Mapping `(ratio − 0.5) × 2` pushed all vowels to the negative side. Recentered at observed mean: `(ratio − 0.25) × 3.5`. Tightened F2 band to bins 7–17 (skip /u/'s borderline F2 ~1100 Hz). Dropped analyser `smoothingTimeConstant` 0.8 → 0.3 for crisper vowel transitions in fast Japanese syllables.

**37 — Mouth lingered after audio ended.** RAF only checked `audio.paused || audio.ended` — browser fires `ended` slightly after audible signal stops (MP3 decode padding), and inter-syllable silences smeared because of slow `DECAY_FACTOR=0.18`. Two-layer fix: (a) silence-aware decay — when peak < 0.012, switch to `SILENCE_DECAY=0.55` (snaps closed in ~14ms); (b) explicit `audio.addEventListener('ended', fadeMouthClosed)` and `'pause'` → forces close immediately when audio actually stops. `MOUTH_FADE_MS` 150 → 100ms for snappier post-utterance close.

### Calibration (final values)
- `AMPLITUDE_GAIN = 3` (linear, was 10 with pow curve)
- `ATTACK_FACTOR = 0.8`, `DECAY_FACTOR = 0.18`, `SILENCE_DECAY = 0.55`, `SILENCE_THRESHOLD = 0.012`
- `MOUTH_FADE_MS = 100`, `MOUTH_DEAD_ZONE = 0.03`
- `VOWEL_SMOOTH = 0.4`, `VOWEL_FORM_SCALE = 0.7`
- `VOWEL_RATIO_CENTER = 0.25`, `VOWEL_RATIO_GAIN = 3.5`
- `analyser.smoothingTimeConstant = 0.3`
- `IDLE_FORM = -0.49` (matches idle motion's `ParamMouthForm` rest value)
- Speech/idle blend: `speechWeight = min(1, mo × 2)` (sharp transition so vowel shapes aren't washed out by idle when mouthY is moderate)

### Files changed
- `amadeus.html` — single file, all changes confined to lip sync analysis pipeline:
  - Constants block (~line 622) — added formant + silence-aware decay constants
  - `ensureAudioContext` (~line 1488) — eager init, lipFreqArray allocation, smoothingTimeConstant
  - `lipTick` RAF inside `playSyncedAudio` (~line 1582) — peak amplitude + F1/F2 analysis + silence-aware smoothing + explicit 'ended'/'pause' listeners
  - Parameter index map (~line 1191) — added `'ParamMouthForm':'mouthForm'`, multi-strategy Cubism 5 scan
  - `beforeModelUpdate` listener (~line 1245) — linear amplitude → mouthY, vowelForm → mouthForm with sharp speech/idle blend

### Working principle reinforced
"Think before coding — surface concerns BEFORE writing code." Spent significant time guessing wrong fixes (`lipSyncValue` write, direct ticker writes) before reading the actual library source code to find `'beforeModelUpdate'`. Lesson: when fighting a framework, *read the framework first*. `grep -oE 'emit\("[A-Za-z]+' on the minified library surfaced the correct hook in 2 minutes.

### Outstanding/deferred
- None. Lip sync feels natural per user testing — vowel-shape variation visible, mouth syncs cleanly with Japanese audio, no lingering between sentences.

---

## May 1, 2026 (Obsidian MCP Integration)

**Claude Code session.** No code changes to Amadeus itself — infrastructure/tooling session.

### What was set up
- **`@bitbonsai/mcpvault`** connected to Claude Code as the `obsidian` MCP server
- Vault path: `/Users/zha61/Documents/Amadeus/docs`
- Config location: `~/.claude.json` → `mcpServers.obsidian` (NOT `~/.claude/settings.json`)
- Full npx path required: `/opt/homebrew/bin/npx`

### Three issues hit before it worked
1. **Wrong env var** — mcpvault takes the vault path as a positional arg, not a `VAULT_PATH` env var. Fixed: moved path to `args` array.
2. **Wrong PATH** — Claude Code desktop app (launched via app icon) doesn't inherit shell `$PATH`, so `npx` was not found. Fixed: hardcoded `/opt/homebrew/bin/npx` as the command. Same pattern as Bug #19 (Electron PATH issue).
3. **Wrong config file** — `~/.claude/settings.json` is for permissions/model/env config, not MCP servers. MCP servers go in `~/.claude.json`. Fixed: moved `mcpServers` block there.

### Package chosen: `@bitbonsai/mcpvault` (over `obsidian-mcp` and `@modelcontextprotocol/server-filesystem`)
- Last npm publish April 2026 (more current than `obsidian-mcp`'s Oct 2025)
- Native append mode — essential for `session-log.md` and `bugs.md` workflow
- Frontmatter-aware, 12 open issues vs 25 for `obsidian-mcp`
- Official `server-filesystem` considered but lacks append and frontmatter support

### Files changed (outside Amadeus repo)
- `~/.claude/settings.json` — created (correct format, wrong file — left in place, harmless)
- `~/.claude.json` — added `mcpServers.obsidian` block at top level

### CLAUDE.md updated this session
- "Update docs at session end" → replaced with concrete per-action rules
- New "MCP Tools Available" section added with config details and usage notes

### Tests run
- List vault: ✅ all 9 docs visible
- Write (overwrite): ✅
- Write (append): ✅ two lines present, in order
- Delete: ✅ sandbox file removed

---

# Session Log — Amadeus Project

---

## April 30, 2026 (Saya birthday + tiered absence + freshness + sleep-hours + planning docs)

**Chat session, not Claude Code.** Four small improvements shipped to `amadeus.html`. Three planning docs created for future Claude Code sessions. No backend changes, no rebuild needed.

### Improvement A — Saya birthday dialogue (June 11)
- Added `Birthday: 11 June` to ABOUT SAYA section in SYSTEM_PROMPT (durable fact, British date format)
- Three new greeting arrays: `GREETINGS_SAYA_BIRTHDAY` (4 entries, on-the-day), `GREETINGS_SAYA_BIRTHDAY_EVE` (3 entries, June 10), `GREETINGS_SAYA_BIRTHDAY_AFTER` (3 entries, June 12)
- Three new date checks in `pickGreeting()`. Birthdays take precedence over absence detection and time-of-day. Mixed tonal spread per array (mostly tsundere with at least one openly warm entry).

### Improvement B — Tiered absence detection
- New localStorage key: `amadeus_last_seen` (timestamp ms). Read on every boot, computes gap, writes current time back.
- Three tier arrays: `GREETINGS_SHORT_AWAY` (24-72h), `GREETINGS_MEDIUM_AWAY` (3-14d), `GREETINGS_LONG_AWAY` (14d+) — 3 entries each.
- Wrapped in try/catch — corrupt or disabled localStorage silently skips absence detection, never crashes greeting flow.
- Defensive read guards: `!isNaN && lastSeen > 0 && lastSeen <= nowMs` (rejects garbage and future timestamps from clock changes).
- Birthdays always win over absence — intentional design choice.

### Improvement C — Greeting freshness memory
- New localStorage key: `amadeus_recent_greetings` (JSON object: `{arrayName: [recentIndices]}`)
- New `pickFresh(arr, arrName)` helper replaces all 11 random-pick calls in `pickGreeting()`
- Cap: 3 recent indices per array (or `floor(len/3)` for small arrays — formula prevents over-blocking small pools, e.g. floor(3/3)=1 means a 3-entry array remembers only the last pick)
- Defensive: corrupt JSON / missing storage / fully-blocked candidate pool all fall through gracefully (defaults back to full range pick)
- Result: same greeting won't repeat back-to-back across launches

### Improvement D — Sleep-hours awareness
Two parts shipped together:
- **(a) New `GREETINGS_SMALL_HOURS` array** (4 entries) for hours 01:00-04:59. Split out of the old NIGHT branch which now covers 21:00-00:59 only. Heavier concern register than late-evening NIGHT.
- **(b) New `formatTimeContext()` function** — injects a context note at the *end* of system prompt during 01:00-04:59: "CURRENT CONTEXT: It is the early hours of the morning for Saya — he should be asleep. If conversation goes long, gently push back about it (in your tsundere way) without nagging. One mention is enough."
- `buildSystemPrompt()` rewritten to handle both memory injection (existing) and time-context append (new). Empty memory + non-late-night returns SYSTEM_PROMPT byte-identical — zero regression for the common case.
- Token cost: ~30 tokens, only during 01:00-04:59 hours.

### Improvement E — British date format
- `Birthday: June 11` → `Birthday: 11 June` in ABOUT SAYA section. One line change.
- Code-level date checks unchanged (always used numeric `month===6 && day===11` etc.)

### Bug-prevention checks performed
- 13 unique greeting `const` declarations (no duplicate-`const` JS crash risk per bug 4)
- All emotion tags in canonical 20-emotion list, no risky-bleed tags (`melancholic`/`thinking`/`embarrassed`/`flustered`) in any new array
- All 10 critical anchors from CLAUDE.md verified intact: parsEmo signature, playSyncedAudio signature, think:false, 127.0.0.1 (not localhost), audio_b64 check, finally block, IME isComposing handling, CHARACTER anchor, numeric birthday checks
- localStorage namespacing clean — two distinct new keys (`amadeus_last_seen`, `amadeus_recent_greetings`), no collisions

### Tests Saya ran (all passed)
- Boot regression — app starts, video plays, transitions to UI
- Send/receive — Kurisu responds with text + TTS + expression change
- IME/textarea clear after Enter
- Diary save on close
- Memory injection on relaunch

### Tests deferred / not done
- Bug 23 (expression decay not firing) — investigated, code looks structurally correct, decided not to "fix" something not reproducibly broken. Saya's call.
- Time-dependent features (birthday/absence/late-night) not directly verified — they require clock manipulation or fake localStorage values. Code-level verification was done via diff and test scripts.

### Planning docs created (in `docs/`)
- `roadmap-rag-vn.md` — Phase 1 VN-only RAG with phased Phase 2 diary integration. Open question flagged at top: does Saya have an English VN transcript or only Japanese audio transcripts?
- `roadmap-obsidian-mcp.md` — Recommends direct-filesystem MCP server (e.g. `obsidian-mcp` or `@bitbonsai/mcpvault`) over Local REST API + bridge approach.
- `roadmap-lip-sync.md` — Web Audio API amplitude analysis driving Live2D `ParamMouthOpenY`. Single-file change to `amadeus.html`. Forward-compatible if/when Fish Audio adds `char_timings`.

### Notable conversation: prompt-size research
A substantive research conversation happened about ideal system-prompt length. Captured here so it doesn't get re-litigated:
- No published "ideal token count" exists for character prompts. Variant B at ~1280 tokens (~1630 with memory) is well within working ranges per Anthropic guidance ("smallest effective"), Lost-in-the-Middle research, and the Talk Less Call Right (arXiv 2025) roleplay paper (which favored more structure over less length).
- Chroma's "Context Rot" paper (Hong et al., July 2025) shows degradation with input length even below context-window saturation, but tested retrieval tasks not character coherence.
- Past-Opus's "300 token target" claim from earlier sessions was, per its own later admission, sourced from a single Substack newsletter, not peer-reviewed research.
- Working principle reinforced: trust empirical evals over any cited token threshold. Don't add to the prompt what JS can do.

### Manual cleanup item
`AMADEUS_PROJECT.md` flagged for **deletion** (its own header notes redundancy with `REFERENCE.md`, parts are stale referencing gemma3:12b and "April 23 status"). Historical info preserved in this session log.

### File deltas
- `amadeus.html`: 1902 → 2065 lines (+163 lines, all additive or clean refactor)
- No other code files modified

---

## April 28, 2026 (Stage 1 Session Memory + Variant B + Many Fixes)

**Major feature shipped:** Stage 1 session memory (sliding window of 7 most-recent diary entries injected into system prompt).

### Variant B prompt rewrite (replacing previous prompt)
- Reduced textbook word usage from 9/15 baseline → 0/15 in testing
- Reduced trailing-question frequency from 12/15 → 3/15
- Reduced fabrication regressions from 12/15 → 0/15
- Structure: 25 casual examples (vs 9 before), explicit "casual words during emotional moments" rule, expanded INPUT→EMOTION mapping, dropped problematic `[annoyed] Hello.` example
- See `kurisu-personality.md` for full text

### parsEmo fix
- Old: strict regex matching exact emotion list — when gemma4 invented tags like `[concerned]`, they leaked into displayed subtitles
- New: `validEmotions = new Set(...)`, regex matches ANY `[word]`, only adopts known emotions but strips ALL bracketed tags
- Tested with 13 cases including `[concerned]`, `[worried]`, etc.

### ABOUT SAYA section added
- Stores durable user facts: name, age (18), occupation (Student), location (England), interests (rhythm games / 音ゲーム, anime, football, piano, chess)
- Constraint paragraph: reference naturally, do not invent specifics beyond the list
- Replaces vague "you don't know specifics" workaround with actual structured facts

### Pronoun update for Saya
- Changed she/her → he/him in 4 places in SYSTEM_PROMPT
- Preserved Kurisu's self-references about original Kurisu (lines 423, 544) untouched
- Diary system prompt has no pronoun references — works for any gender

### RECENT CONVERSATIONS caveat
- Added paragraph after WHAT YOU KNOW ABOUT SAYA explaining diary entries are impressions, possibly embellished
- Counters the topic-fabrication issue where Kurisu treated past diary's narrative details as established facts

### Greetings completely rewritten
- 25 generic + 8×4 time-of-day arrays (was 16 + ~5 each)
- ~16% address Saya by name (target was 15-20%)
- AVOIDS risky emotion tags: no `melancholic`, `thinking`, `embarrassed`, `flustered` in greetings (these can leak English in audio)
- Tone: casual, tsundere, cheerful (happy), neutral (calm/default)
- Match Variant B casual register (simple words, varied openers, statement-ending mostly)
- BIRTHDAY array kept untouched

### Phase 1 — Memory injection
- `MEMORY_WINDOW_SIZE = 7`, `formatMemorySection()`, `buildSystemPrompt()` added near diary functions in `amadeus.html`
- One-line change in `sendMsg`: `content:SYSTEM_PROMPT` → `content:buildSystemPrompt()`
- Reads diary entries from localStorage, formats up to 7 most-recent, injects at `\nCHARACTER\n` regex anchor
- Defensive: `Array.isArray` guard on diary data, console.warn if anchor missing, defaults missing date to "(unknown date)"
- Empty memory → byte-identical to original prompt (zero regression)

### Phase 2 — IPC plumbing
- `preload.js` full replacement: 5-line stub → 28 lines exposing 5 IPC channels via contextBridge
- `amadeus.html` additions: IPC handlers wrapped in single `if (window.electronAPI)` guard, "SAVING SESSION" overlay HTML element (placed just before `</body>`, outside `#window-wrap`), sendMsg overlay-visibility guard
- `main.js`: only added `ipcMain` to electron destructured imports
- Channel names: `request-conversation`, `conversation-response`, `save-diary-entry`, `diary-save-complete`, `show-saving-overlay`

### Phase 3 — Diary-on-close coordinator
- `main.js` adds `runDiaryOnClose()` (orchestrator) + `runDiaryWithExit()` (shared exit-with-diary)
- New `mainWindow.on('close')` handler intercepts X-button path
- Refactored `app.on('before-quit')` handler intercepts Cmd+Q path
- Both check `diaryHandled && !diaryInProgress` to prevent close-mid-save (Bug #9 fix)
- 30s total timeout, 25s inner Ollama AbortController
- Force-clears `diaryInProgress` in `runDiaryWithExit` after race so `app.quit()` can pass guards (Bug #16 fix)
- Model name passed via IPC from renderer (single source of truth)
- All 4 critical scenarios traced: Cmd+Q happy path, X-button, double-X-click during save, timeout case

### IME/textarea fix
- Bug: text in input box sometimes didn't disappear after Enter (macOS autocomplete/IME committing AFTER our handler cleared the value)
- Fix: `e.isComposing||e.keyCode===229` check + `clearMsgInput()` helper that clears sync AND on next tick
- Same fix applied to send-button click path

### Ollama auto-start fix (latent bug exposed by Test 6)
- Bug: `spawn('ollama', ...)` failed with ENOENT because Electron doesn't inherit Terminal PATH
- Fix: hardcoded `const OLLAMA = '/usr/local/bin/ollama'` constant (same pattern as PYTHON)
- Defensive: spawn wrapped in try/catch + ollamaProc.on('error', ...) listener so ENOENT doesn't crash app with popup
- Was latent because Ollama was usually already running from previous sessions

### Fish Audio tag rewrites (English-bleed bug 22 follow-ups)
- Original `curious` fix from earlier session was already in place
- New: rewrote `thinking`, `melancholic`, `embarrassed`, `blush` tags using fragment grammar
- Applied same heuristic: gerund-start clauses ("speaking slowly with X") and verb-particle endings ("breaking through") tend to leak; noun/adjective fragments stay safe as instruction
- Triggered by Saya hearing English bleed on the "The late hours" greeting which had `melancholic` emotion

### Bug-finding methodology
- Three rounds of fresh-eyes review of design doc (v3 → v3.1 → v3.2)
- Each round caught real bugs the previous missed (X-button bypass, double-close race, timeout deadlock)
- All fixed before any code was written

### Tests run by Saya
- Test 1 (empty memory regression): PASS
- Test 2 (memory injection works): PASS, output verified
- Test 3 (no voice regression): PASS, 0 textbook words
- Test 4 (diary-on-close happy path): PASS
- Test 5 (no-conversation close): PASS
- Test 6 (dead Ollama timeout): PASS (exposed latent OLLAMA path bug, fixed)
- Test 7 (X-button close): PASS
- Test 8 (memory injection still works post-Phase-3): PASS
- Test 9 (no regressions): PASS

### Decisions deferred
- Bug 23 (expression decay not firing) — deferred until reproducible
- Reset button — kept as-is (defense in depth, different intent than Cmd+Q)
- Concurrent Ollama call risk if user sends chat then Cmd+Q immediately — acknowledged limitation
- `package.json` `files` whitelist still references `kurisu_elevenlabs_server.py` instead of `kurisu_fish_server.py` — pre-existing, doesn't affect personal use

---

## April 23, 2026
- Switched model from gemma3:12b → gemma4:latest
  - gemma4 has native system role support and improved instruction following
  - Ollama 0.21.0 confirmed — flash attention safe and re-enabled
  - think:false added to all Ollama API calls to disable thinking mode
  - num_ctx increased 4096 → 8192 (system prompt ~1278 tokens needs headroom)
  - Think token stripping added to ollamaStream (channel-style, pipe-style, standard fallback)
  - Empty text guard (finalText fallback) added before ttsSpeak
- System prompt completely rewritten — lean character card structure (~1278 tokens, down from 2627)
  - USER section: Saya (サヤ), ask about daily life, meals, sleep, exams
  - TWO MODES: CASUAL (default, ≤35 words, simple everyday words) / ACADEMIC (≤70 words)
  - CASUAL WORD RULE: concrete substitution examples (not "inefficient" → "not good for you")
  - WARMTH section reconciled: warmth is reluctant but real, Saya has earned it
  - INPUT→EMOTION mapping: labelled as emotion-tag-only, separate from TWO MODES
  - Greeting/casual mapped to [tsundere] or [happy]
  - ROMANTIC/FEELINGS hard rule: always [flustered] or [tsundere], never answer directly
  - BAD EXAMPLE: "Hello" → monologue explicitly labelled wrong with reason
  - GOOD EXAMPLES: casual, academic, emotional categories, Saya's name in examples
  - Two new examples: academic (prefrontal cortex) + identity (very detailed impression)
- Few-shot examples restructured with CASUAL/ACADEMIC/EMOTIONAL labels
- Personality improvements: input→output emotion mapping, do-not-sanitise rule, do-not-break-character anchor
- Kurisu addresses user as Saya (サヤ) throughout
- Debugged gemma4 silent response issue:
  - Root cause: gemma4 thinking mode puts content in message.thinking not message.content
  - Fix: think:false in API call + think token stripping + finalText guard
- main.js: flash attention disabled then re-enabled after confirming Ollama 0.21.0

---

## April 19, 2026
- Implemented expression decay in amadeus.html (setEmo function)
  - Added EMO_DECAY_MS map: short (4s) for surprised/scared/angry/excited/flustered,
    medium (7s) for happy/tsundere/embarrassed/annoyed/teasing/smug,
    long (12s) for sad/melancholic
  - Intellectual/neutral emotions have no decay — hold until next response
  - emoDecayTimer added as state variable alongside emoTransitionTimer
  - Decay resets whenever a new emotion is set, unlocks idle variety once expired
- Confirmed birthday dialogue (July 25) was already implemented
- Rotated Fish Audio and DeepL API keys
- Fixed bug 20: DeepL API key variable not used in Authorization header
- Fixed bug 21: EMOTION_OPENER tags vocalised by Fish Audio as English speech — removed

---

## April 16, 2026
- Set up Obsidian vault pointing at docs/ folder for Claude Code persistent memory
- Rewrote system prompt with WARMTH RULE, tsundere arc, 70-word limit, strict [EMOTION:X] format
- Rewrote all 19 Fish Audio emotion tags as voice actor directions
- Added EMOTION_SPEED map and compute_speed() function (6-condition dynamic speed)
- Added add_prosody_tags() function with emotion-conditional prosody injection
- Fixed re-anchor guard: len(parts) >= 2
- Set normalize: False in Fish Audio payload
- Updated Fish Audio API params: temperature 0.8, top_p 0.8, repetition_penalty 1.1
- Fixed subtitle sync: audio-duration-based via loadedmetadata (replaced 280ms/word timer)
- Fixed wordCount ReferenceError, fragile word split, import random location
- Removed sarcastic from SIGH_EMOTIONS

---

## April 15, 2026
- Created AMADEUS_PROJECT.md as master state document
- Set up Obsidian vault in docs/ for Claude Code memory
- Created structured docs: session-log, kurisu-personality, bugs, roadmap

---

## April 13-15, 2026 (Long session)
- Switched TTS from ElevenLabs to Fish Audio S2 Pro cloud API
- Settled on neutral baseline voice (c4d832799bf845ee86638a1bc0cd0d41) + rich emotion tags
- Expanded emotion system from 11 to 19 emotions
- Fixed Fish Audio char_timings: null bug
- Fixed playSyncedAudio argument order bug
- Fixed parsEmo() destructuring bug
- Fixed duplicate const declarations in sendMsg() crashing JS entirely
- Fixed subtitle sync — word-by-word wall clock timer (280ms/word), independent of audio
- Greeting sync working on boot with voice
- Blink system updated: flustered=rapid, melancholic=slow
- isLoading now resets in finally block
- Flash attention enabled: OLLAMA_FLASH_ATTENTION=1
- Cache auto-clears on every launch
- Attempted Ollama translation (Option B) — caused cold-start timeouts, reverted to DeepL
- DeepL auth fixed: header-based auth (form body deprecated Nov 2025)
- Kurisu name TTS fixed: kanji to katakana
- Ollama changed from localhost to 127.0.0.1 (CORS fix)

---

## Earlier (pre-April 13)
- Initial Electron app scaffolding
- Live2D Cubism 4 integration with PixiJS 6.5.2
- Boot video with 12s fallback
- Ollama gemma3:12b chosen over deepseek-r1:8b
- Python path hardcoded to /opt/homebrew/bin/python3
- Fish Speech S2 local attempted — abandoned (requires ~20GB RAM)
- ElevenLabs as original TTS — kept as backup
- Session diary + BGM added
- System prompt with agentic proactivity + anti-platitude rule
- Live2D expressions + EMO_POSTURE for all emotions

## Session — May 3, 2026 (evening) — VN Transcript RAG Phase 1

**Goal:** Implement dual-corpus RAG to improve Kurisu's tonal authenticity per `roadmap-rag-vn.md`, with architecture change to use two corpora instead of one.

**What shipped:**
- `build_kurisu_index.py` — one-shot ingestion script; reads Japanese corpus (756 clips, `~/Documents/Kurisu_Dataset_Pro/metadata.csv`) and English corpus (1672 LP lines, `~/Desktop/kurisu_english_lines.csv`); embeds both with `bge-m3` (Ollama); persists two ChromaDB collections (`kurisu_ja`, `kurisu_en`) to `~/Documents/Amadeus/data/chroma/` (~13.8 MB on disk). Run time: ~44s.
- `kurisu_rag_server.py` — Flask on port 5003; loads both collections at startup; warm-up embed call to pre-load bge-m3; `/health` GET for main.js polling; `/retrieve` POST takes `{query, k}`, embeds English query, returns `{ja: [...], en: [...]}` top-k from each collection.
- `main.js` — spawns `kurisu_rag_server.py` alongside Fish server (port 5003, stale-kill pattern); kills on `stopServices()`; replaced flat 8s `setTimeout(createWindow)` with async `waitForRagServer()` health poll (500ms × 20 attempts = 10s max, falls through on timeout so chat works without RAG).
- `amadeus.html` — added `fetchRagContext(query)` (1.5s timeout, silent fallback on failure); `formatRetrievedSection(ragContext)` (two labelled blocks: EN style examples + JA voice anchors); `buildSystemPrompt(ragContext=null)` updated to accept and append retrieved section. Only `sendMsg()` gets RAG — `ttsGreeting` and `generateDiaryEntry` use bare `SYSTEM_PROMPT` unchanged.

**Architecture decisions:**
- k=3 per collection (6 lines total injected). Token budget: ~220-240 tokens worst-case. Total with memory + late-night context: ~1870 tokens, well under 8192 num_ctx.
- English lines injected first (more direct signal), Japanese second (tonal anchor).
- English framing: "STYLE EXAMPLES — match rhythm, sharpness, characteristic phrasing"
- Japanese framing: "VOICE ANCHORS — tonal reference only, do NOT translate, do NOT quote, do NOT respond in Japanese"
- RAG section appended after time context (recency bias for both).

**Corpus path correction:** roadmap said `~/Desktop/Kurisu_Dataset_Pro/` — actual path is `~/Documents/Kurisu_Dataset_Pro/`. Fixed in scripts.

**pip note:** chromadb must be installed into `/opt/homebrew/bin/python3` (the PYTHON constant), not the system Python 3.14. Command: `/opt/homebrew/bin/pip3 install --break-system-packages chromadb`

**Files changed:** `build_kurisu_index.py` (new), `kurisu_rag_server.py` (new), `main.js` (rebuild done), `amadeus.html` (no rebuild needed)

## Phase 1 RAG Evaluation — May 3, 2026 (post-launch)

**Result: PASS.** Saya's assessment after live testing:
- Responses noticeably more authentic
- Conversations flow like actual conversation rather than isolated turn-by-turn responses
- Topic switching is smooth — no register drift between science/casual/emotional
- Overall: "good improvement"

**Verdict:** Phase 1 evaluation criteria met. Phase 2 (diary RAG integration) is now unblocked if wanted. Recommend running a few more sessions before committing to Phase 2 — current improvement may be sufficient for a while.

## May 9, 2026 — Red UI revert

### Summary
Reverted `amadeus.html` from the cyan/video-background state back to the original red Steins;Gate palette. No functional changes to LLM, TTS, RAG, or lip-sync.

### Changes made
- **CSS variables** restored to original red palette: `--bg:#060404`, `--blue:#c0392b`, `--blue-bright:#e84040`, `--red:#c0392b`, `--grid:rgba(192,57,43,0.10)`, `--text:#f0c8c8`, etc.
- **`#glitch-h1,#glitch-h2`** restored: height 1px→2px, background `rgba(232,64,64,0.5)` / `rgba(100,200,255,0.3)`
- **`.t-line.lit`** restored to `#e84040`
- **`#app::before`** restored to red CSS grid (`background-image:linear-gradient(var(--grid)...)`, `background-size:32px 32px`)
- **Removed `.bg-full` CSS block** (and the multi-line comment explaining it)
- **Removed `#amadeus-bg{display:none;}`** — restored as `position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;` (transparent stub canvas)
- **Removed `#app::after` vignette** CSS (radial-gradient darkening)
- **Removed `#app .crt-lines` CSS** (extra scanline overlay added for video aesthetic)
- **Removed `filter:blur(0.5px) contrast(1.04) saturate(0.96)`** from `#live2d-canvas`
- **Removed `<video class="bg-full">` HTML element** and comment
- **Removed entire canvas IIFE** (`initAmadeusBg`) — ~17 KB of code. Canvas was always cyan-palette (no original red version existed); original background was purely CSS grid via `#app::before`
- **Simplified `boot()`** — removed all bg-video playback/watchdog code
- **Boot timeout** reverted 15000→12000ms
- **Hardcoded cyan** in diary overlay and saving-overlay changed to red equivalents (`#e84040`, `rgba(232,64,64,...)`)
- **L-shape corner indicators** stay removed (removed in the previous session, kept removed)
- **`kurisu_fish_server.py` calm tag fix** preserved (fragment style `[calm, measured, unhurried, clear]`)
- File shrunk from ~2600 lines to ~2319 lines

## May 9, 2026 — Boot Video Reliability (AUDIO_RENDERER_ERROR root cause + pipeline fixes)

**Goal:** Diagnose and fix intermittent boot video failure on quick relaunch. Symptom: black screen instead of boot video; sometimes Kurisu's voice completely silent for the whole session even if the video eventually loaded.

### Root cause A — `process.exit(0)` orphaning Electron audio service (AUDIO_RENDERER_ERROR)

The primary culprit was a hard `process.exit(0)` call in `mainWindow.on('closed')` and `window-all-closed`. This kills only the Electron **main process** — child processes (audio service, GPU service) are orphaned and stay alive. The audio service child holds macOS CoreAudio's exclusive device lock. When a new Amadeus instance launches within a few seconds, its audio renderer tries to initialize CoreAudio — which is still locked — and fails with `AUDIO_RENDERER_ERROR`. This error permanently breaks ALL audio in that Chromium session: boot video audio AND Kurisu's TTS voice, for the entire run.

**Fix:** Removed all `process.exit(0)` from close handlers. Let Electron's natural quit sequence proceed — `app.quit()` → `will-quit` fires proper IPC shutdown messages to all child processes, which release CoreAudio before exiting. Added a `will-quit` safety valve: 5s `setTimeout(() => process.exit(0), ...)` with `.unref()` so it fires only if Electron's shutdown stalls, but never prematurely interrupts audio release. 2s was too short (had been set to 2s) — increased to 5s.

**Symptom that revealed this:** Screenshot showed `AUDIO_RENDERER_ERROR` in Electron's DevTools. After this error, UI and Live2D model appeared normally but complete silence on TTS.

### Root cause B — `preload="auto"` + `vid.load()` double-load race

Boot video element had `preload="auto"`. Browser immediately starts fetching the video on HTML parse. Then `boot()` calls `vid.load()` which **aborts** the in-flight preload and starts a new fetch. `loadeddata` could fire for the aborted fetch, not the new one, causing the `playBootVideo()` await to resolve with stale state — video never actually played, boot transitioned to Kurisu with blank screen.

**Fix:** Changed to `preload="none"`. Now only the `vid.load()` call in `playBootVideo()` triggers the fetch, and the `loadeddata` listener is always wired for that single load. No race.

### Root cause C — Protocol handler missing HTTP range request support

The `amadeus-asset://` protocol handler served video via `fs.readFile()` + `new Response(buffer)`. HTML5 `<video>` issues **HTTP range requests** (`Range: bytes=X-Y`) for progressive/seeking loads. A plain `Response(buffer)` doesn't send `Accept-Ranges` headers and can't fulfill range requests — the video element received no response for its range request and stalled. This caused intermittent cold-boot failures completely unrelated to CoreAudio.

**Fix:** Replaced `fs.readFile + new Response(buffer)` with `net.fetch(pathToFileURL(resolved).href, { bypassCustomProtocolHandlers: true })`. Electron's native file fetcher supports proper HTTP range requests, so `<video>` can seek and stream correctly.

### Root cause D — `error` listener during playback cutting video short

`playBootVideo()` had an `error` event listener on the video element during the playback wait phase. A transient audio initialization hiccup (which can happen during early CoreAudio recovery) fired the `error` event on the video element — not a real load error, just an audio renderer complaint — which resolved the wait promise early. Video was cut mid-play before the natural `ended` event.

**Fix:** Removed `error` listener from the playback wait phase. Only `ended` + 14s safety timeout can end the wait. If video genuinely can't load, timeout catches it — transient audio events no longer abort playback.

### Secondary fix — `beforeunload` audio cleanup

Added `window.addEventListener('beforeunload', ...)` in the renderer: pauses and clears `src` on all `<audio>` and `<video>` elements, calls `audioCtx.close()`. This ensures CoreAudio is released from the renderer side before Electron's child processes handle it from their side — belt-and-suspenders for clean audio handoff on relaunch.

### Boot sequence architecture (final, clean)

```
playBootVideo()           — loads via amadeus-asset://, plays fully, only ended/timeout can end it
  ↓
fade boot screen          — 0.6s opacity transition
  ↓
reveal Kurisu + UI        — app.style.opacity='1', startBGMOnce(), initLive2D()
  ↓
ttsGreeting()             — pickGreeting(), setEmo(), TTS call
```

`playBootVideo()` falls back to `muted=true` if audio renderer failed to initialize — video still plays visually; never blocks the boot sequence.

### Files changed
- `main.js`: removed `process.exit(0)` from `closed`/`window-all-closed`, `will-quit` safety valve increased to 5s with `.unref()`, protocol handler changed to `net.fetch(pathToFileURL(...))` (range support), added `pathToFileURL` import from `url`
- `amadeus.html`: `preload="none"` on boot video element, `playBootVideo()` isolated function (muted fallback, no `error` listener during playback), `boot()` refactored to clean 4-step sequence, `beforeunload` audio cleanup added, removed red diagnostic overlay (`#boot-diag`), removed `clearCache()` calls, removed `exitedAt`-based wait logic

### Bugs added to bugs.md
#38 — `process.exit(0)` orphans audio service → AUDIO_RENDERER_ERROR
#39 — `preload="auto"` + `vid.load()` double-load race
#40 — Protocol handler missing HTTP range request support
#41 — `error` event listener during playback cuts video short
#42 — `beforeunload` audio cleanup needed for CoreAudio release

## May 10–11, 2026 — Voice Input (MLX Whisper)

**Goal:** Add voice input mode using MLX Whisper medium model. Replace existing Web Speech API stub with a proper local transcription pipeline.

### What shipped

**New file: `kurisu_whisper_server.py`**
- Flask on port 5004, `mlx-community/whisper-medium-mlx`, `language='en'`
- Background warmup thread pre-loads model at startup (stdlib WAV + `wave` module — no soundfile needed)
- `threading.Event` (`model_ready`) gates transcriptions until model is loaded — up to 5min timeout covers first-run download
- `threaded=True` Flask so warmup and transcription don't deadlock
- PATH fix: `/opt/homebrew/bin` prepended before imports so mlx_whisper's internal `ffmpeg` subprocess resolves

**`main.js`** (rebuild done):
- `whisperProcess` added alongside `ttsProcess`/`ragProcess`
- Stale-kill port 5004 before spawn; killed in `stopServices()`
- Spawned 15s after window open (keeps model warmup I/O from competing with boot video)
- CoreAudio gap timer added: reads `.last-exit` timestamp, waits up to 3s before `createWindow()` on quick relaunch — prevents AUDIO_RENDERER_ERROR on fast restart

**`amadeus.html`** (no rebuild):
- Replaced Web Speech API (`initSpeech`/`stopListen`) with `startRecording()`/`stopRecording()` using `MediaRecorder` + fetch to port 5004
- UX: click mic → "Recording..." → click again → spinning dots (`dotBounce` CSS animation in `v-trans`) → transcript appears with Send button → user reviews → click Send → `sendMsg()`
- 30s `AbortController` timeout on transcription fetch; error distinguishes AbortError from server error
- `v-send` button added to voice panel HTML (hidden until transcript ready)

### Bugs fixed during this session

**ffmpeg PATH** — mlx_whisper calls ffmpeg as subprocess; Electron spawn doesn't inherit shell PATH so `/opt/homebrew/bin/ffmpeg` wasn't found → empty transcripts. Fixed by prepending `/opt/homebrew/bin` to `os.environ['PATH']` before imports in the server (same class as bugs 10/19/27).

**BGM stops/changes track during voice recording** — macOS audio session switches to record+playback on `getUserMedia` and back on track stop. This paused `bgmAudio` AND could fire `ended` prematurely, advancing to the next song. Fixed with `bgmInterrupted` flag (set synchronously at session change, cleared 800ms after resume). `onended`/`onerror` in `initBGM` replay current track if flag is set. BGM + AudioContext resumed via `setTimeout` at both recording start (100ms) and stop (200ms).

**Boot video unreliable — clicking window fixed it** — `ensureAudioContext()` was only called inside `initLive2D()`, which runs *after* the boot video finishes. Audio renderer wasn't kicked before video started. Click triggered `ensureAudioContext()` (wired to 'click' listener) which resumed it. Fixed by calling `ensureAudioContext()` at the very top of `boot()` before `playBootVideo()`.

**Mic not released on close-while-recording** — `beforeunload` didn't stop `mediaRecorder` tracks. Chromium would have released them on renderer destruction, but added explicit stop for clean audio session release ordering (same pattern as explicit `audioCtx.close()`).

### Files changed
- `kurisu_whisper_server.py` — new
- `main.js` — rebuilt
- `amadeus.html` — no rebuild

### Tests (all passed)
- Voice recording → transcription → Send → Kurisu responds normally
- BGM continues playing during and after recording
- Boot video plays reliably on quick relaunch
- Close while recording mid-session: no errors, diary saves normally

### mlx-whisper install
```
/opt/homebrew/bin/pip3 install --break-system-packages mlx-whisper
```
Model pre-downloaded via:
```
/opt/homebrew/bin/python3 -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/whisper-medium-mlx')"
```
Cached at `~/.cache/huggingface/` (~1.5 GB, one-time).

---

## May 11, 2026 — Boot video mid-play freeze fix (Bug 43)

**Symptom:** On quick relaunch, boot video occasionally stopped mid-play with the screen frozen for ~14 seconds before boot proceeded. Sometimes the video didn't play at all (silent/black).

**Root cause:** Bug 41's fix correctly removed the `error` listener from the playback wait phase to prevent transient audio events from cutting the video short. But it left a gap: when `AUDIO_RENDERER_ERROR` fires mid-playback (CoreAudio still releasing from the previous session), the video element stops silently — `ended` never fires, and the full 14s safety timeout was the only exit. The load-phase muted fallback didn't help because by then `vid.play()` had already succeeded and we were past the for loop.

**Fix (`amadeus.html`, no rebuild):** Added a one-shot `error` listener in the playback wait phase that restarts the video muted from the beginning (`vid.muted=true`, `vid.currentTime=0`, `vid.play()`). The error handler does **not** resolve — only `ended` or the safety timeouts do (preserves bug 41's constraint). A second 12s timeout covers the muted replay path; a `done` guard ensures only the first resolution counts.

**Bug 43 added to bugs.md.**

---

## May 11, 2026 — Diary-on-close missing think:false (Bug 13 regression fix)

**Symptom:** Diary entry not saved on close — diary button showed latest entry as May 9 even after having a full conversation.

**Root cause:** The diary Ollama call in `runDiaryOnClose()` (main.js Step 2) was missing `think: false` at the top level. Without it, gemma4:latest enters thinking mode and returns its response in `message.thinking` instead of `message.content`. `entryText = result.message?.content || null` resolved to `null`, hitting the `if (!entryText) return` guard and silently skipping the save. This was dormant since the diary-on-close was written (April 28) but became consistent after a likely gemma4 model update.

**Fix:** Added `think: false` to the diary Ollama call in main.js (Step 2). Rebuild done. One-line change.

---

## May 11, 2026 — RAG Phase 2: Diary Corpus Integration

**Goal:** Add diary entries as a third searchable RAG corpus so Kurisu can semantically recall older conversations by topic, complementing the Stage 1 sliding window (recent 7) and Stage 2 long-term impressions summary.

### Architecture (Option 2A — additive)

Three memory layers, each serving a different role:
- `LONG-TERM IMPRESSIONS` — broad emotional patterns, always injected (Stage 2)
- `RECENT CONVERSATIONS` — last 7 sessions verbatim, always injected (Stage 1)
- `RELEVANT PAST MOMENTS` — semantically matched older entries, per-turn (Phase 2, new)

### What shipped

**`kurisu_rag_server.py`** (no rebuild):
- Added `get_embeddings_batch(texts)` helper — single Ollama API call for all docs (vs N individual calls); much faster for 50-entry diary
- New `/index-diary` endpoint: validates input, `get_or_create_collection('amadeus_diary')`, builds ids/docs/metas (ID = `entry.date` or `entry_{i}` fallback), batch-embeds + upserts. Idempotent. Returns `{"status":"ok","indexed":N}`.
- Extended `/retrieve`: adds diary retrieval block in its own inner `try/except` after ja/en. `get_collection` throws if collection missing (fresh install) — caught silently → `diary:[]`. Guards `n_results = min(2, col.count())` before query. Response shape extended to `{ja:[...], en:[...], diary:[...]}`. Outer except also updated to include `diary:[]`.

**`amadeus.html`** (no rebuild):
- `formatRetrievedSection()`: added `diaryLines` computation, updated early-return guard to include diary (`&& diaryLines.length === 0`), added RELEVANT PAST MOMENTS block after ja block
- `indexDiaryInBackground()` helper: reads `loadDiary()`, returns immediately if empty, POSTs to `/index-diary` with 3s AbortController timeout, all errors caught silently with `console.log`
- Call site 1: end of `boot()` after `ttsGreeting` is fired — fire-and-forget
- Call site 2: `onSaveDiarySummary` finally block after `diarySummarySaved()` — re-indexes once both new diary entry and summary are saved

### Fresh-install / empty diary path (verified)
`loadDiary()` → `[]` → `indexDiaryInBackground()` returns immediately, no fetch → `amadeus_diary` collection never created → `/retrieve` `get_collection` throws → caught silently → `diary:[]` → `formatRetrievedSection` injects nothing → behaviour identical to current. Zero console errors.

### Token budget
k=2 diary entries ≈ 100–150 tokens. Worst case total (all layers active): ~2100 tokens. Well under 8192 num_ctx.

### Anchors verified
parsEmo, playSyncedAudio(text, audioBase64, emotion), think:false in sendMsg, 127.0.0.1, audio_b64 check, isLoading in finally, isComposing, CHARACTER anchor, numeric birthday checks, beforeModelUpdate hook — all intact.

---

## May 11, 2026 — Startup lag fixes (RAG/Whisper deferred, launchctl async)

**Symptom:** Opening Amadeus caused system-wide lag on MacBook Pro 16GB, contributing to boot video stalls.

**Three root causes identified:**

1. **RAG server spawned at T=0** — `kurisu_rag_server.py` immediately loads ChromaDB and runs a bge-m3 warm-up embed (CPU/disk-heavy, ~10s startup). This competed directly with the boot video loading and playing.

2. **Whisper server spawned at T+15s** — boot video is done by ~10s, but at 15s the greeting TTS is still playing and Live2D is active. The 1.5 GB model load hit disk mid-greeting.

3. **`launchctl setenv` calls were `execSync`** — two blocking Node.js event-loop freezes on startup (100–300ms each). Belt-and-suspenders for externally-started Ollama; no reason to block.

**Fixes (`main.js`, rebuild):**
- Added `exec` to child_process imports
- Changed both `launchctl setenv` calls from `execSync` to fire-and-forget `exec(..., () => {})`
- Moved RAG server spawn out of `startServices()` into a `setTimeout(..., 20000)` in `app.whenReady()` — after boot video + greeting are fully done. `waitForRagServer()` now called inside that setTimeout.
- Moved Whisper server spawn from T+15s → T+30s — 10s after RAG, so bge-m3 and whisper-medium don't load from disk simultaneously.

**Service startup timeline (new):**
- T=0s: TTS server + http.server spawn (needed immediately for greeting + boot)
- T=3–5s: window opens, boot video plays
- T=20s: RAG server spawns + background health poll
- T=30s: Whisper server spawns
- First user message typically arrives at T=30–60s → RAG ready in time

---

## May 11, 2026 — Stage 2 Session Memory (rolled-up diary summary)

**Goal:** When total diary entries exceed the 7-entry sliding window, older entries were silently dropped. Stage 2 adds a pre-computed compressed summary of all entries older than the window so Kurisu retains long-term impressions across many sessions.

### What shipped

**`preload.js`** (rebuild):
- 4 new IPC bindings: `onRequestDiaryEntries` / `sendDiaryEntries` (main asks renderer for full entries + watermark), `onSaveDiarySummary` / `diarySummarySaved` (main pushes generated summary back to renderer)

**`main.js`** (rebuild):
- `DIARY_TIMEOUT_MS` raised 15 000 → 40 000 ms (sequential budget: diary Ollama ≤12s + summary Ollama ≤12s + IPC round-trips ≤8s + 8s headroom)
- `SUMMARY_FETCH_TIMEOUT_MS = 12000`, `MEMORY_WINDOW_SIZE = 7` constants added
- `runDiaryOnClose()` gains Step 4 after diary-save-complete: asks renderer for `{ entries, watermark }` → if `entries.length > 7 && entries.length > watermark` → Ollama summary call (`think:false`, `num_predict:100`, temp 0.7, gemma4) → pushes `{ summary, watermark: entries.length }` to renderer

**`amadeus.html`** (no rebuild):
- `formatLongTermImpressions()` — reads `amadeus_diary_summary` from localStorage, returns `\nLONG-TERM IMPRESSIONS:\n<text>\n` or `''`, full try/catch
- `buildSystemPrompt()` updated: combines long-term block + recent block before injecting at CHARACTER anchor (long-term first, separated by blank line, then RECENT CONVERSATIONS)
- Two new IPC handlers inside `if (window.electronAPI)`: `onRequestDiaryEntries` (reads diary + watermark, sends both), `onSaveDiarySummary` (writes both localStorage keys, acks via `diarySummarySaved`)

### New localStorage keys
- `amadeus_diary_summary` — the pre-computed summary string (~100 tokens)
- `amadeus_diary_summary_watermark` — stringified integer; equals `entries.length` at last generation; prevents redundant Ollama calls when nothing new has fallen outside the window

### Design decisions
- **Sequential (option b)** over parallel for summary + diary — no concurrent Ollama calls on 16 GB RAM
- Entries are newest-first in storage; `slice(7).reverse()` feeds Ollama oldest-first for chronological summary
- Empty-summary path is byte-identical to Stage 1 behaviour — zero regression when < 8 total entries
- `think:false` on summary Ollama call (new code, not touching existing diary call which is pre-existing)
- Budget choice flagged: 40s outer race covers worst-case sequential without orphaning the close sequence

### Anchors verified (all intact)
parsEmo signature, playSyncedAudio(text, audioBase64, emotion), think:false in sendMsg, 127.0.0.1 (not localhost), audio_b64 check (no char_timings), isLoading reset in finally, e.isComposing IME guard, CHARACTER anchor in SYSTEM_PROMPT, numeric birthday checks, beforeModelUpdate lip sync hook

### Files changed
- `preload.js` — rebuilt
- `main.js` — rebuilt
- `amadeus.html` — no rebuild needed

---

## May 16, 2026 — Boot Video Reliability, Prewarm Overhaul, Fish Audio Tag Fix, File Cleanup

### First-message lag — root cause found and fixed

The May 15 prewarm fix eliminated cold-load lag but the num_ctx mismatch meant KV cache was never actually reused. Full fix shipped across two files:

**`amadeus.html`:**
- `prewarmOllama()` — added `num_ctx: 8192` to match `sendMsg()`. Without this, Ollama reallocated the KV buffer on every first message (different context size = different buffer = no cache hit). Also replaced the `'hi'` placeholder with `buildSystemPrompt('')` so the full system prompt is in the cache before the user types anything.
- Fires at the very top of `boot()` in both paths (normal + incoming call), before `playBootVideo()`, so prewarm runs during boot video dead time.

**`main.js`:**
- `prewarmOllamaMain(signal)` — new function. Polls `/api/tags` until Ollama is up (max 10 × 500ms), then fires a single `num_predict:1` chat call to load gemma4 into RAM before the window opens.
- Startup sequence: `startServices()` → start prewarm → `Promise.all([waitForHttpServer(), 5s timer])` → `prewarmAbort.abort()` → `createWindow()`. The AbortController cancels main's prewarm at exactly 5s — prevents a stale main-process request arriving after the renderer's system-prompt prewarm and evicting the useful KV cache.
- `waitForHttpServer()` returns in ~200ms on warm relaunch — the `Promise.all` 5s timer guarantees the minimum delay regardless.

### Boot video — two reliability fixes

Both fixes in `amadeus.html` (`playBootVideo()`):

1. **Always attempt `vid.play()`** — removed the `if(ready)` guard that could skip play() after a transient error event. Video always tries to play.
2. **Early-exit on stalled load** — added `if(vid.paused && vid.readyState < 2) return` to avoid waiting for an `ended` event on a video that never started loading.

Also removed the dead bge-m3 unload inner try/catch from `indexDiaryInBackground()` (leftover from an earlier approach — bge-m3 eviction already handled elsewhere).

### Fish Audio curious tag — acoustic-anchor rule

**Bug:** `curious` EMOTION_TAG contained the fragment `genuine engaged interest throughout`. Fish Audio vocalised it as English speech — user heard "...genuine engage" spoken before the Japanese response.

**Root cause analysis:** Every safe EMOTION_TAG fragment is grounded in an acoustic or physical anchor — `voice`, `pitch`, `pace`, `words`, `delivery`, `quality`, `brightness`, `edge`, `lift`, etc. Fish Audio recognises these as voice-direction vocabulary. `genuine engaged interest throughout` had no such anchor — it described a pure internal mental state. The trailing adverb `throughout` made it read as a complete, self-contained statement, not a direction fragment. Fish Audio treated it as speech content.

**Fix:** Replaced with `intent investigative edge` — adjective + adjective + quality noun. Parallel to `analytical brightness` (already in same tag). Each word is unambiguously a voice-direction fragment.

**Rule confirmed for future tag writing:** Every EMOTION_TAG comma-fragment must end in an acoustic-anchor noun (`quality`, `brightness`, `edge`, `lift`, `pace`, `intensity`, `texture`, `delivery`, `voice`, `pitch`, `form`). Fragments ending in adverbs (`throughout`, `always`, `constantly`) or describing internal states with no acoustic referent will be vocalised.

Final curious tag:
```
[leaning-forward quality, analytical brightness, quickening pace as interest catches, intent investigative edge, questioning lift even on statements]
```

### File cleanup — legacy files moved to Trash

The following files had no active references and were moved to `~/.Trash/` (recoverable):
- `kurisu_voice_setup.py` — old voice model setup script
- `launch_amadeus.py` — old launcher (superseded by `open ...Amadeus.app`)
- `launch_amadeus.sh` — old launcher
- `start_amadeus.sh` — old launcher
- `variant_b_revised.txt` — system prompt working draft from April 25; content now in `amadeus.html`
- `session_memory_design_v1.md` — v1 design doc from April 25; superseded by `docs/` architecture
- `claudeignore` — stray file (not `.claudeignore`), unused
- All `.DS_Store` files outside build dirs

`kurisu_elevenlabs_server.py` retained for now — still referenced in `package.json` build files list (line 44 must be cleaned before next `npm run build`, or it will include the dead file in the app bundle).

### Files changed
- `amadeus.html` — no rebuild needed
- `main.js` — rebuild required (`npm run build`)
- `kurisu_fish_server.py` — no rebuild needed, relaunch only

---

## May 16, 2026 (later) — Conversation History Sliding Window

**Symptom:** `history` array grew unbounded during a session. Every Ollama call spread the full array into `messages` — by turn 30, prefill processed 30 exchanges of tokens, progressively slowing every reply.

### What shipped (`amadeus.html` — no rebuild)

**Added `HISTORY_WINDOW=30` constant** (line 385, alongside `OLLAMA_MODEL`).

**Changed Ollama call** (line 1937):
```javascript
// before
messages:[{role:'system',content:buildSystemPrompt(ragCtx)},...history],
// after
messages:[{role:'system',content:buildSystemPrompt(ragCtx)},...history.slice(-HISTORY_WINDOW)],
```

### Window size rationale (30 messages = 15 exchanges)

- 30 × ~120 tokens/exchange = ~3600 tokens of history
- + system prompt ~1630 + RAG ~450 = ~5680 tokens total
- `num_ctx: 8192` → 2512 tokens headroom; `num_predict: 120` so reply never approaches it
- Chosen over the initial 20-message suggestion: 10 exchanges felt thin for flowing sessions; 15 exchanges covers most natural conversation arcs
- Performance impact of the extra 10 messages: ~400–600ms extra prefill on M5 (gemma4 prefills ~2000–3000 tok/s) — invisible behind Fish Audio's ~1–2s TTS latency

### What stays untouched (verified)

The `history` array itself remains unbounded. Only the slice passed to Ollama is trimmed:
- Line 2077 — Reset handler `history=[]` unchanged
- Line 2271 — `generateDiaryEntry` still uses full `history.map()`
- Line 2518 — diary IPC handler still uses full `history.map()` so close-time diary generation sees the entire session

Kurisu's memory of older turns remains intact via the existing layers: 7 diary entries injected at `\nCHARACTER\n` anchor + RAG VOICE ANCHORS/STYLE EXAMPLES + system prompt context. Raw history beyond turn 15 is just additional fidelity — not the only memory source.

### Files changed
- `amadeus.html` — no rebuild needed

---

## May 16, 2026 (post-window-fix bug sweep) — Three Latent Bugs Found and Fixed

Triggered a full audit after the HISTORY_WINDOW change. Three real bugs surfaced plus one stale comment.

### Bug A — `generateDiaryEntry` missing `think: false` (amadeus.html line 2284)

**Symptom:** When user clicked Reset, `generateDiaryEntry()` fired an Ollama call without `think: false`. gemma4 could emit `<|channel>thought...<channel|>` tokens into the diary entry. The line-2285 regex strip only handles `[EMOTION:X]` prefix — channel-style thinking tokens would leak into stored diary entries.

**Fix:** Added `think:false` to the options object. Now consistent with main.js's diary-on-close path (line 112) and the renderer's `ollamaStream` (line 1868).

### Bug B — Diary conversation slice kept the BEGINNING instead of the end (amadeus.html lines 2274 + 2522)

**Symptom:** Both `generateDiaryEntry` (Reset path) and the diary IPC handler (close path) used `slice(0, 1800)` to truncate conversation history before passing to the diary generator. On long sessions, this discarded the most recent ~3200 chars and kept only the opening 1800 — diary reflected the conversation's start, not its arc.

**Fix:** Changed to `slice(-1800)` in both places. Becomes more important now that HISTORY_WINDOW=30 explicitly supports longer sessions.

### Bug C — Orphan user message in history on Ollama error (amadeus.html line 1969)

**Symptom:** `sendMsg()` pushes `{role:'user'}` at line 1914 BEFORE the Ollama fetch. If Ollama errored (timeout, network failure, parse error), the catch block ran without popping the orphan user message. Next turn sent two consecutive user messages to Ollama. gemma4 usually tolerates this but it's an invalid state.

**Fix:** Added defensive pop at the top of the catch block:
```javascript
if(history.length>0 && history[history.length-1].role==='user') history.pop()
```

Role-check guard ensures we never accidentally pop an assistant entry — only fires when the orphan user is actually the last entry.

### Bonus — Stale comment correction (amadeus.html line 1945)

Comment said *"Flash attention is disabled in main.js"* but main.js line 320 explicitly sets `OLLAMA_FLASH_ATTENTION = '1'`. Corrected to *"Flash attention is enabled in main.js — safe with Ollama ≥0.20.4"*.

### Cross-file consistency verified
- All 6 Ollama API call sites now have `think: false` (main.js × 3, amadeus.html × 3)
- main.js diary handler is content-agnostic to the slice direction — change is transparent
- ttsSpeak is fire-and-forget (not awaited) so its errors don't reach sendMsg's catch — no false `history.pop()` triggers
- Reset flow unchanged: `generateDiaryEntry()` reads history BEFORE `history=[]` clears it

### Files changed
- `amadeus.html` — no rebuild needed, relaunch only

---

## May 16, 2026 (RAG timeout fix) — fetchRagContext timeout 1500ms → 4000ms

**File:** `amadeus.html` line 2431 — no rebuild needed.

Increased the RAG retrieval abort timeout from 1500ms to 4000ms. bge-m3 embedding under memory pressure (gemma4 resident at 8192 num_ctx) can exceed 1500ms on cold or semi-cold first calls, causing silent RAG fallback — Kurisu loses all style examples and voice anchors for that message. 4000ms gives bge-m3 comfortable headroom; subsequent RAG calls within the session are near-instant so the higher ceiling has no practical per-turn cost. Tradeoff: worst-case first-message wait increases by up to 2.5s, which is better than silently degraded character accuracy.

---

## May 17, 2026 — Web Search (Amadeus Internet Research)

Kurisu can now answer questions about current events by searching the web.

### Architecture

Keyword trigger in `sendMsg()` — fires only when the message contains time-sensitive words (`new`, `latest`, `upcoming`, `movie`, `anime`, `2025`, `2026`, etc.). On match, RAG and web search run in **parallel** via `Promise.all` — no serial wait. Non-matching messages are completely unaffected.

```
sendMsg()
├── needsWeb = keyword regex test (instant)
└── Promise.all([fetchRagContext(M), needsWeb ? fetchWebContext(M) : null])
    └── buildSystemPrompt(ragCtx, webResults) → Ollama
```

### What was built

**`kurisu_rag_server.py`** — new `/web-search` endpoint:
- `duckduckgo-search` library (no API key, installed via pip)
- Takes `{query}`, runs DDG text search, returns 3–5 bullet strings truncated to ~120 chars each
- 3s internal timeout via DDGS, full silent failure returns `{"results": []}`

**`amadeus.html`** — three additions:
- `fetchWebContext(query)` — calls `/web-search`, 5s AbortController timeout, returns array or null
- Keyword trigger + `Promise.all` in `sendMsg()` replacing the single `fetchRagContext` await
- `buildSystemPrompt(ragContext=null, webContext=null)` — new optional second param; injects `CURRENT WORLD CONTEXT` block last (maximum recency bias) when non-empty. All existing callers (`prewarmOllama`, diary) pass no second arg → default null → no change.

### System prompt clarification injected with web results
> "Your March 2010 knowledge cutoff applies to Steins;Gate in-universe events only — real-world information provided here is current and accurate."

### Token cost
3–5 bullets × ~30 tokens each = ~90–150 tokens added when web fires. Total prompt stays well under `num_ctx:8192`.

### Why this approach over speculative pre-fetch
Original plan fetched web context during TTS dead time of turn M for use at turn M+1 — always one turn stale, always fired even when not needed, and injected boot-time news irrelevant to the conversation. This approach: same-turn, on-demand, triggered only when relevant. Web-triggered messages add ~1–2s before Ollama starts; unaffected messages have zero added latency.

### Files changed
- `kurisu_rag_server.py` — relaunch only
- `amadeus.html` — relaunch only
- `duckduckgo-search` pip package installed

---

## June 2026 — Relationship Depth Arc

Kurisu's warmth now shifts across accumulated sessions (item 1 of the Claude-chat "less boring" list). Implicit by design — no visible meter. All in `amadeus.html` (relaunch only).

### Design
- **5 stages** on a cumulative score: Guarded (0) → Thawing (5) → Familiar (15) → Close (35) → Bonded (65). `REL_STAGE_THRESHOLDS=[0,5,15,35,65]`.
- **Engagement-weighted, not tone-weighted** — chose engagement after reasoning about the feedback trap (rewarding warm phrasing would teach the user to perform warmth to "level up"). Score grows from *showing up and talking*, not from what's said.
- **Scoring:** +0.5 base per genuine new session (gap ≥30 min), applied on the FIRST exchange (not boot) so a silent open-and-close earns nothing; plus +0.05/exchange capped +1.0/session. Net 0.5–1.5 per active session → ~65 sessions to Bonded (slow / earned).
- **Slow pacing + mild reunion coolness** chosen over fast/no-decay: absence ≥14 days drops one stage at boot, but only if stage ≥2.

### Architecture (key decisions)
- **Stage frozen at boot** in `initRelationship()` (runs before `prewarmOllama()`). The directive text is therefore byte-identical all session, preserving the prewarm KV-cache prefix (bugs 33/34). Score keeps accruing live in the background; the stage only re-reads next boot. This is the crux that makes the feature zero-lag.
- `relationshipDirective()` → stage-specific `RELATIONSHIP` block injected before the `\nTWO MODES\n` anchor in `buildSystemPrompt()` (mirrors the existing memory-injection pattern). Each stage anchors what does NOT change (tsundere core, deflection, covering warmth) and only modulates how easily/often warmth slips. "Bonded" ≠ soft — she stops performing distance she doesn't feel while staying sharp and allergic to sappiness.
- **State:** localStorage `amadeus_relationship={score,sessions,sessionExchanges}`. `bumpRelationshipEngagement()` fires after `history.push({role:'assistant'})` in `sendMsg()` — one tiny localStorage read+write, after generation, can't block the user.

### Drawback-reduction fixes (same session)
- **First-run seed capped:** `Math.min(seedSessions, 34)` from diary history — caps at Familiar so long-time users don't teleport to Bonded.
- **Reunion-coolness guard:** only drops a stage if stage ≥2 (a Guarded relationship can't get colder).
- **Anchored directives:** every stage re-states the unchanging tsundere core so a high stage can't drift into out-of-character softness.
- **Debug tool:** `window.showAmadeusRelationship()` → console.table of stage/score/sessions/progress.
- **Exchange-gated base credit:** moved the +0.5 from boot to first-exchange (the silent-open fix), gated by `_relIsNewSession`.

### Bug fixed alongside
- **Incoming-call paths never wrote `amadeus_last_seen`** — previously only `pickGreeting()` wrote it, so accepting a call (and the in-session incoming-call handler) left last_seen stale, breaking both absence greetings and the new reunion-coolness detection. Now written in both the incoming-call boot path and the in-session handler.

### State at session end
score 34.5 = Stage 2 (Familiar), 0.5 from Close.

---

## June 15, 2026 — Diary reflections reflect relationship stage (follow-up #2)

Closed the consistency gap where diary entries were generated with the bare diary prompt regardless of stage — so even at a warm stage her private nightly reflections read in the Guarded-default voice.

### What changed
- New `buildDiarySystemPrompt()` in `amadeus.html`: base diary prompt + a stage-specific voice modifier indexed by `_relActiveStage`. The private arc is her *internal honesty with herself* (Stage 0 analytical/suppressed → Stage 4 tender/guard-down), deliberately distinct from her chat-facing performance — the diary is where she can drop the act.
- **Both diary paths covered:**
  - `generateDiaryEntry()` (renderer inline / Reset button) → calls `buildDiarySystemPrompt()` directly.
  - Diary-on-close (Ollama runs in `main.js`) → renderer now includes `diarySystemPrompt: buildDiarySystemPrompt()` in the `conversation-response` IPC payload; `main.js` destructures it into `diarySysContent` and uses it, falling back to the original hardcoded string if absent (backward-safe).
- `preload.js` unchanged — `sendConversation` forwards the payload object verbatim, so the new key passes through.

### Scope discipline
Exactly 6 edit sites (3 in `amadeus.html`, 3 in `main.js`), nothing else touched. Verified by simulating `buildDiarySystemPrompt()` output at all 5 stages and grepping every reference. `sendMsg`, `buildSystemPrompt`, `initRelationship`, `bumpRelationshipEngagement` all untouched.

### Files changed
- `amadeus.html` — relaunch only
- `main.js` — **rebuilt** (`npm run build`)
