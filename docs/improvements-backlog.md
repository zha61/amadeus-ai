# Improvements Backlog — Amadeus

Compiled July 13, 2026 after full-codebase review (amadeus.html, main.js, preload.js,
kurisu_fish_server.py, kurisu_rag_server.py, kurisu_whisper_server.py,
build_kurisu_index.py, package.json). 150 concrete items, globally numbered —
say "implement #N" to pick one. Ordered within category by rough value.
Not reviewed in depth yet: `scheduler/` + call-window.html + preload_call.js (see #90).

## A. Conversation quality / brain (1–30)

1. Tune `STYLE_THRESHOLD` (0.7 was a first guess) from real `[rag] en/ja: dists=` logs after a week of use
2. Tune `BEHAVIOR_THRESHOLD` (0.5) the same way — borderline matches unknown
3. ✅ DONE (Jul 18) — Persist which behavior rule fires per message to a rotating log file (console-only now, lost on close)
4. Allow top-2 behavior rules when both clear threshold (e.g. project + tired can co-occur)
5. New behavior rule: user asks for advice / help deciding
6. New behavior rule: user finished/shipped something (distinct from starting a project)
7. New behavior rule: user is bored / asks what to do
8. New behavior rule: user asks about HER day — needs a consistent self-narrative answer
9. Add invented-context guard: bake-off showed models inventing exams/school events not mentioned
10. ✅ DONE (Jul 18) — Stock-phrase fatigue: detect repeated deflections ("Don't get the wrong idea", "W-what") per session; prompt rule or post-check
11. Topic-tagged diary recall (roadmap #3) — tag entries (chess, 音ゲー, football) for specific callbacks
12. Semantic dedupe of retrieved style lines — 3 near-identical lines waste prompt tokens
13. Dynamic RAG token budget — cap injected lines by token count, not line count
14. Compress older in-window diary entries (entry-level summarization before the stage-2 rollup)
15. Session-opener continuity: greeting can reference last session's closing topic (diary already has it)
16. HISTORY_WINDOW: token-based windowing instead of fixed 30 messages
17. parsEmo: map invented-but-close tags ([worried]→scared) via synonym table instead of discarding to default
18. Emotion-tag distribution telemetry per session — detect tsundere-lock
19. Trim EXAMPLES block (~50 lines) to the 15 strongest — ~700 tokens less per call, faster prefill; verify with harness
20. A/B temperature 0.75–0.8 — game_money meanness was partly sampling variance
21. Harness-verify the CASUAL banned-words list actually suppresses clinical words
22. Calendar / exam-period context injection (roadmap #4)
23. Weekday awareness in time context ("Monday, school tomorrow")
24. Optional weather context via free API — she comments on his real weather (privacy: location)
25. ✅ DONE (Jul 18) — `relStatus()` console helper printing stage/score/exchanges
26. Reunion coolness could also pick a cooler greeting, not just a lower stage directive
27. Multi-turn probes for the harness (all current probes are single-turn)
28. Automatic rubric scorer for harness outputs (word count, banned words, tag validity) → prompt-change regression testing
29. Track her question-asking ratio vs the "1 in 4" target
30. ✅ DONE (Jul 18) — Remove dead `EMOTION_OPENER` dict from fish server (unused since bug 14 fix)

## B. Voice / TTS (31–48)

31. A/B a narrow emotion-speed band (sad/melancholic 1.05) vs V3's flat 1.1 — flat may rush sad lines
32. ✅ DONE (Jul 13) — Pre-synthesize + cache greeting audio to disk (fixed strings) — instant boot voice, saves Fish credits. ⚠️ **It never HIT until 2026-09-27** — the read path lacked `data/` (bugs.md 91).
33. Emergency TTS fallback when Fish fails (macOS `say` JP voice, or clean text-only mode)
34. ✅ DONE (Jul 18) — `ttsSpeak` had no fetch timeout — hung request waits forever; add ~20s AbortController
35. Log TTS latency per call; flag sustained >5s
36. Trim leading/trailing silence from Fish MP3s server-side (ffmpeg silenceremove) — snappier feel
37. Use DeepL's glossary API for name/term protection instead of string replaces
38. DeepL free tier = 500K chars/month — log cumulative usage, warn at 80%
39. ✅ DONE (Jul 13) — DeepL failure currently sends ENGLISH to Fish (spoken with EN accent) — retry once then text-only instead
40. A/B normalize:True specifically on long greeting lines
41. Per-emotion Fish temperature (calm 0.6, flustered 0.8) — test after V3 settles
42. Strategic 、 insertion post-translation for phrasing control (native prosody instead of tags)
43. Regenerate Fish voice model from multiple reference samples for consistency
44. Re-verify subtitle msPerWord math after normalize change (audio durations shifted)
45. (scope-check) Whisper `language='en'` hardcoded — fine while he speaks English only
46. ✅ DONE (Jul 18) — Surface Whisper `no_speech_prob`/`avg_logprob` (Phase 2 gate — designed, unbuilt)
47. Mic level meter in the voice panel while recording
48. Rapid double-send hard-cuts her mid-word — consider 150ms fade-out instead

## C. Voice-first (49–56)

49. ✅ DONE (Jul 18, Silero v5 primary + RMS fallback) — Phase 2 VAD: band-limited adaptive RMS + hysteresis + onset confirmation (fully designed)
50. ✅ DONE (Jul 18) — Whisper gate on no-speech probability (designed, pairs with #46)
51. ✅ DONE (Jul 18) — Auto re-arm mic on her reply 'ended' (designed)
52. Push-to-talk (hold Space) as alternative to VAD
53. Phase 3 barge-in — deferred; revisit only if the loop feels like it needs interrupting
54. Subtle chime when mic re-arms (hands-free state feedback)
55. Configurable auto-send delay (700ms constant now)
56. ✅ DONE (Jul 18) — Hands-free auto-exit after ~10 min of no speech

## D. Live2D / visual (57–72)

57. Inventory all motions in model3.json — idle variety currently uses only 'Special' ×2
58. Emotion-driven breathing rate (melancholic slower, excited faster)
59. (big, note only) webcam gaze tracking option
60. Parallax grid background reacting subtly to mouse depth
61. Look-away micro-behavior while speaking tsundere lines (posture tied to speaking state)
62. Blink less during speech (humans do)
63. Round parameter writes to kill sub-pixel jitter
64. Tiny emotion glyph in side panel (label currently hidden entirely)
65. `sub-jp` element appears unused — either add JP subtitle toggle or remove
66. Time-of-day ambient tint (evening = warmer grid)
67. Kurisu-flash micro-effect on strong emotion transitions
68. macOS vibrancy/translucency experiment
69. Verify canvas devicePixelRatio handling at all window sizes
70. Deduplicate '...' placeholder vs typing-indicator mechanisms
71. Diary overlay: search/filter box
72. Diary overlay: export-to-markdown button

## E. Boot / performance / stability (73–87)

73. ✅ DONE (Jul 13, via bug 58 fix) — Instrument video 'waiting' events to confirm the blob prebuffer killed stalls
74. Log prewarm abort/retry outcomes for tuning
75. Lazy-load Live2D SDK scripts during boot video (parallelize startup)
76. Replace python http.server with amadeus-asset:// for the whole app — kills port 8765 races and one child process
77. Measure keep_alive '30m' vs '2h' — mid-session eviction vs memory pressure
78. Measure bge-m3 reload pattern — eviction-after-index may cause per-message cold hits
79. ✅ DONE (Jul 13) — Pre-fetch greeting TTS during the boot video window — she speaks the instant she appears (pairs with #32)
80. ✅ DONE (Jul 18) — Service watchdog in main.js — auto-respawn crashed fish/rag/whisper with backoff
81. Renderer error log to file via IPC (post-session debugging without DevTools open)
82. Persist window size/position across launches
83. Drop PIXI ticker to 30fps when idle (no speech/mouse) — battery
84. Poll `ollama ps` after replies; log unexpected model reloads (regression sentinel for the num_ctx family)
85. Friendly first-run message when Ollama isn't installed/running
86. ✅ DONE (Jul 18) — Write `.last-exit` on will-quit too (crash coverage for the CoreAudio gap)
87. (heavy, note only) electron-updater auto-update channel

## F. Features (88–107)

88. Topic-tagged diary recall (= #11, roadmap #3 — listed here as the feature face of it)
89. Exam-period awareness (= #22 feature face)
90. ✅ DONE (Jul 13, findings → #151-152) — audited `scheduler/` + call-window.html + preload_call.js subsystem end-to-end
91. ✅ DONE (Jul 13) — **Vision**: gemma4 has unused image input — paste a screenshot, she comments on it (huge, canon-appropriate)
92. She knows the current BGM track and can remark on it
93. BGM controls in side panel (skip/pause)
94. Tap her → short "what I was just thinking" bubble (reuses proactive machinery)
95. Session stats in diary overlay (streak, message counts)
96. Export conversation transcript
97. Outfit/expression pack switching UI
98. Pomodoro / study-with-me mode with check-ins (pairs with #89)
99. Daily first-boot briefing (date, her "plans", yesterday callback)
100. Voice-mute toggle (text-only mode for public places)
101. Kurisu birthday (Jul 25) mini-event beyond the greeting array
102. More canon rituals via the Dr Pepper framework (@channel, lab-member number)
103. "Connection quality" flavor meter tied to real server health
104. Edit ABOUT ZANI facts from a settings UI instead of editing the prompt
105. JP subtitle toggle (pairs with #65)
106. Keyboard-only operation + focus-ring accessibility pass
107. First-run onboarding overlay

## G. Robustness (108–119)

108. Cache last RAG query→result for instant retry after transient failure
109. Cap ollamaStream retries at 5 (10×4s = 40s worst case today)
110. Resume partial Ollama streams instead of full retry
111. localStorage quota check — diary+summary growth; migrate to file via IPC if near limits
112. Audit remaining JSON.parse sites for guards (diary/greetings/relationship done)
113. Whisper port-conflict error message (5004 taken)
114. requests.Session + retry adapter in fish server
115. Parallelize the 4 sequential ChromaDB queries in /retrieve (ThreadPoolExecutor)
116. LRU cache for repeated embed queries in RAG server
117. Aggregate /status endpoint combining all three servers' health
118. Recompute idle timers on system wake (sleep drift)
119. Revisit `webSecurity:false` — scope to localhost origins if possible

## H. Code health (120–132)

120. Section-index comment header at top of amadeus.html (single-file navigation)
121. Delete legacy kurisu_elevenlabs_server.py + its package.json files entry
122. package.json bundles the LEGACY server but NOT fish/rag/whisper — align bundle with reality (see #133)
123. Remove bypassed add_prosody_tags/compute_speed code once V3 is settled (or env-flag them)
124. Extract the duplicated BGM-resume guard dance into one helper
125. Move idle/decay magic numbers into the calibration-constants pattern
126. Document amadeus_scheduler.json purpose/shape
127. dev/README.md documenting the three harnesses
128. Standardize console log prefixes; one-line taxonomy doc
129. Full type annotations in the python servers
130. requirements.txt for python deps
131. ✅ DONE (Jul 13) — **git init + .gitignore — the project has no version control; single highest-leverage safety item**
132. Pin exact electron/electron-builder versions

## I. Packaging (133–137)

133. Self-contained .app (bundle python servers or document the source-dir dependency)
134. Code signing (build shows 0 identities)
135. DMG appearance polish
136. Verify build-scheduler chain still works
137. Bundle size audit (music/video/live2d)

## J. Docs (138–145)

138. CLAUDE.md: fish settings changed by V3 (temp 0.7, normalize True, fixed 1.1 speed); bug 14/15/32 notes reference removed opener path
139. REFERENCE.md TTS section update for V3
140. bugs.md: add this session's finds (num_ctx family, video prebuffer, F4–F13)
141. session-log.md entry for July 13
142. roadmap.md: mark voice-first Phase 1 ✅, refresh
143. Architecture diagram (mermaid) in docs/
144. justfile/Makefile for common ops (relaunch, rebuild, harnesses)
145. Consolidate auto-memory MEMORY.md (obsidian-mcp setup note is stale)

## K. Security / privacy (146–150)

146. ✅ DONE (Jul 13) — Move Fish/DeepL API keys out of source into an untracked config — MUST precede #131 (git init)
147. Rotate both keys if the project is ever shared (they exist in source + logs today)
148. (low) at-rest encryption for diary localStorage
149. Electron hardening audit beyond webSecurity (#119)
150. Replace lsof port-kills with process-name-scoped kills (could currently kill unrelated apps squatting those ports)

## L. From the #90 scheduler audit (151–152) — audit done July 13, 2026; subsystem healthy overall

151. ✅ DONE (Jul 18) — scheduler/main.js: call timer should re-read scheduler and skip if `callFired` already true (sleep/wake race with the hourly check can fire a call already marked fired)
152. ✅ DONE (Jul 18) — scheduler/main.js: timer callback writes captured `today` — firing after midnight records yesterday's date, permitting a second call the same day; recompute date at fire time

## M. From the August 18, 2026 code examination (153–158)

Findings from a read-only sweep of `amadeus.html`, `main.js` and the three python
servers. Numbers here were measured from source on that date, not estimated.

153. **Sentence-pipelined speech — DEFERRED by Zani, August 18, 2026.** Not a
     rejection: he judged the current speech pipeline good enough for now. Do not
     start this without a fresh decision from him. Full analysis preserved so a
     future session need not redo it:
     - **Today's path is fully serial:** `amadeus.html:2317` awaits the ENTIRE Ollama
       stream (its `onToken` callback is deliberately empty), `:2351` makes ONE
       `ttsSpeak` call with the complete reply, and `kurisu_fish_server.py:473`
       does one translation + one Fish call returning one whole MP3. Nothing is
       audible until every stage finishes.
     - **Option A (split the English mid-stream, translate + synthesize per
       sentence) — REJECTED.** It fires N gemma4 translate calls *while gemma4 is
       still generating*, on the same GPU that renders her Live2D. That is exactly
       what CLAUDE.md rule 37 / bugs.md 61 exist to prevent (measured 0.66s of
       animation-stuttering saturation per translate call). It also loses the
       register-aware translation quality that won the July 18 A/B 7/8, which
       depends on translating with full context.
     - **Option B (translate ONCE on the full text, pipeline only the Fish
       synthesis) — the recommended shape if this is ever built.** No extra gemma4
       load, no GPU contention, translation quality unchanged.
     - **Realistic win is smaller than the July 20 note claimed.** Anchor from
       bugs.md 63: translation 0.85s + Fish 1.27s for ONE short greeting sentence —
       so Fish per-call cost is mostly fixed overhead, not proportional to length.
       Option B therefore saves **0s on a one-sentence reply**, ~0.5–1.5s on two,
       ~1.5–3s on three or four. The "5–9s → 2–3s" figure in the July 20 session-log
       entry describes Option A, which is the rejected one.
     - **Prerequisite (Phase 0):** log sentence-count and per-stage timings for one
       evening first. She is capped at `num_predict:120` with CASUAL ≤35 words, so if
       most replies are single-sentence the ceiling on this feature is ~1s.
     - **Design note:** chunk on a MINIMUM LENGTH, not on every full stop — a
       four-word sentence still costs ~1s of fixed Fish overhead.
     - **Known blockers in the renderer:** `playSyncedAudio` is destructive on entry
       (`amadeus.html:1851` pauses the previous audio, cancels the lip-sync RAF,
       resets the mouth), so it cannot simply be called per sentence; it also clears
       the whole subtitle, and its BGM duck/unduck and its `ended`/`pause` →
       `fadeMouthClosed()` wiring (bugs.md 26/37) are bound to a single element. A
       queue must own utterance-level state while each clip stays a plain `<audio>`.
     - **Unfixable-by-design risk:** per-sentence synthesis resets Fish's prosodic
       contour at every boundary (today `add_prosody_tags` re-anchors *within* one
       utterance — bugs.md 18), plus a 30–100ms MP3 encoder seam between clips. It
       may simply sound choppier. That is an ear test, not a calculation.
     - **Revert design (already worked out):** touch ONLY `amadeus.html` and
       `kurisu_fish_server.py` — neither needs `npm run build`, and the packaged app
       serves both from `AMADEUS_DIR` (`main.js:21`), so revert is a git checkout
       plus a relaunch. Add a `PIPELINE_TTS` runtime flag, keep `ttsSpeak` and
       `/speak` intact as the fallback, work on a branch, tag the pre-work commit.

154. ✅ **DONE (Aug 18, 2026) — bugs.md 68. Measured 672ms → 176ms prefill per turn.** *(Original finding:)* **KV cache: the volatile RAG block sits ahead of the whole history.**
     `amadeus.html:2305` builds `[{system: buildSystemPrompt(ragCtx)}, ...history]`,
     and `buildSystemPrompt` appends the retrieved lines at the END of the system
     message — i.e. near the START of the token sequence. The prefix shared with the
     previous turn therefore ends at the RAG block, so the RAG tail plus the ENTIRE
     30-message history is re-prefilled every turn (~1,500 tokens, growing).
     *(Correction, Aug 18: the re-prefill is real and was measured at 672ms vs 176ms, but
     `prompt_eval_count` does NOT reveal it — that field reports TOTAL prompt tokens and is
     unchanged whether the prefix is cached or not. Use `prompt_eval_duration`.)*
     All the KV discipline of bugs.md 33/34/51/52/55b protects the static body and
     then this placement discards the rest. Fix: keep the system message 100% static
     and inject retrieved lines as a separate message immediately before the current
     user turn — the cacheable prefix becomes `[static system][all history]`, which
     only grows. `_pendingMemoryNote` (`amadeus.html:2307`) has the same problem.
     Helps EVERY reply, including one-sentence ones. Needs a live measurement to size
     the win — this is reasoning about Ollama's prefix cache, not a measured result.

155. ✅ **DONE (Aug 18, 2026) — bugs.md 67.** *(Original finding:)* **Nothing detects a truncated reply.** `num_predict:120` caps generation, but
     `ollamaStream` (`amadeus.html:2049`) reads only `message.content` and `obj.done`
     — `done_reason` appears NOWHERE in `amadeus.html` or `main.js` (grep: 0 hits).
     When she hits the cap (most likely in ACADEMIC mode, ≤70 words plus the tag),
     the reply is cut mid-sentence and treated as complete: spoken by Fish, and
     pushed into `history` at `:2341` as her canonical utterance, from where it feeds
     the diary generator and the fact extractor. **A truncation becomes memory.**
     Minimum fix: detect `done_reason === 'length'`, log the real frequency, and trim
     to the last complete sentence before TTS and before the history push.

156. **The system prompt has doubled and nothing tracks the budget.** Measured
     2026-08-18: `SYSTEM_PROMPT` is 9,801 chars ≈ **2,450 tokens**, while
     `REFERENCE.md` and `kurisu-personality.md` both still describe it as "~1,280
     tokens". The EXAMPLES block alone is 3,100 chars — **31% of the prompt**. On top
     of that every turn stacks ≤20 facts (`FACTS_INJECT_MAX`), the long-term summary,
     7 diary entries (`MEMORY_WINDOW_SIZE`), the relationship directive, RAG from four
     collections (~200 tokens of static headers alone) and 30 history messages →
     roughly **4,500–5,000 tokens of the 8,192 `num_ctx`** before she says anything.
     Costs are prefill time every turn (compounds with #154) and instruction pressure
     on an 8B-class model — a plausible contributor to tsundere-lock and the bugs.md
     65 diary monotone. Do telemetry FIRST (log assembled prompt size per turn), then
     trim against evidence with `dev/stage_compare.py`. EXAMPLES 25→12-15 is the
     biggest single lever; RAG could be budgeted by tokens rather than line count.
     **UPDATE 2026-08-31 (#176):** trimming EXAMPLES is a **speed** lever ONLY — treat any
     quality claim for it as refuted. Swapping all 38 exemplars for real VN lines changed her
     output-length distribution not at all (p=0.39). Measured prompt cost per turn from the
     #176 probe: **~3,050 tokens median** with RAG on, against `num_ctx` 8192 — inside the
     4,500–5,000 estimated here, so the budget is less tight than this item assumed.

157. ✅ **DONE (Aug 18, 2026) — `npm run check` / `dev/check.js`.** *(Original finding:)* **No automated check that the app still parses before launch.** `amadeus.html`
     is a single 4,302-line inline `<script>` (211KB of JS in one block).
     `package.json` has start/build/pack/build-scheduler/build-all — no test, no lint,
     no eslint config, no CI, no test files anywhere; devDependencies is just electron
     + electron-builder. The documented failure mode (CLAUDE.md rule 3 / bugs.md 4 — a
     duplicate `const` silently kills ALL JS and the only symptom is the boot video
     sticking) has no guard except noticing at runtime. Fix: `npm run check` that
     extracts the inline script and runs `node --check` on it (~20 lines, zero deps).
     Worth pairing with an assertion that the prompt anchors `\nCHARACTER\n` and
     `\nTWO MODES\n` still exist, since `buildSystemPrompt` only `console.warn`s if
     they move. Cheapest insurance in the list; no behavioural risk.
     **SHIPPED:** `dev/check.js` (zero deps) — parses every inline `<script>` in
     amadeus.html and call-window.html via `node --check` with error lines remapped to
     real file lines, compiles all four python servers via `py_compile`, and asserts both
     prompt anchors appear exactly once. Exit 1 blocks launch. `AMADEUS_DIR` env override
     exists so the checker can be tested against a mutated copy. **Verified by mutation
     test, not by passing:** a duplicate `const ragCtx` was caught and reported at exactly
     the right line (2305), a stray brace was caught, and renaming the `TWO MODES` header
     was caught — all on throwaway copies, never the real files.
     **SELF-TEST (Aug 18):** `dev/check.selftest.js` / `npm run check:selftest` makes that
     mutation test permanent and readable — success prints only green. Rigor elements:
     a CONTROL run on a pristine copy (a broken environment would otherwise make every
     mutant look caught); TARGETED kills (each mutant must be caught by ITS OWN check kind
     with no collateral, not merely 'something failed'); and one EQUIVALENT mutant — text
     after `</script>`, which must NOT be reported, locking in the boundary that made an
     earlier hand-written test wrong. Asserts run against a new `check.js --json` mode, not
     scraped human text. Meta-verified: sabotaging `bad()` to report nothing, and `ok()` to
     fail everything, both produce SELF-TEST FAILED. Runtime 1.2s.

158. ✅ **DONE (Aug 18, 2026) — bugs.md 66.** *(Original finding:)* **`createMediaElementSource` nodes are never disconnected.** `playSyncedAudio`
     (`amadeus.html:1884`) creates one per reply and connects it to the persistent
     lip-sync analyser; nothing calls `disconnect()`. The audio graph keeps a
     reference, so source nodes accumulate for the life of the session. Slow leak at
     today's 1-per-reply; would be 3–5× worse under #153. Fix: `lipSource.disconnect()`
     in the existing `onAudioStop` handler.

159. ✅ **CLOSED (Aug 26, 2026) — MEASURED, NOT WARRANTED for the prose paths; found bugs.md 73 instead.**
     n=30 per path with the real `SYSTEM_PROMPT`, real history and the real directives:
     `fireProactive` (cap 80) used 19 tokens median / 27 max; `studyTick`'s remark (cap 80)
     18/24; `checkDMails` (cap 120) 20/36. **0/90 truncated, 0/90 ended mid-sentence.** These
     ask for "one short line" and get ~4x headroom, so adding the bug-67 guard would be code
     with no defect to fix. The gate in this entry — "do this once truncation actually
     happens" — was the right call and the answer is no.
     **But checking the JSON paths in the same sweep found a real one: bugs.md 73.**
     `extractFactsNow` at `num_predict:300` truncated 33% of the time on a fact-dense
     conversation, and in JSON mode a truncation is unparseable, so EVERY fact from that
     cycle was silently discarded. Raised to 500 (measured 0/30).
     **Generalisable:** truncation risk is the ratio of the ASK to the cap, not the cap's
     size. 0.8x headroom failed twice (bugs.md 70, 73); 4x headroom never failed.
     *(Original entry:)* **Truncation guard covers only `sendMsg`.** bugs.md 67 added `done_reason` detection
     to `ollamaStream`, which has exactly one call site. The proactive-nudge, canon-remark
     and birthday-gift paths call `/api/chat` directly with `stream:false` (`amadeus.html`
     ~2192, ~2699, ~2985) at `num_predict:80`. Their replies are also spoken and pushed to
     `history`, so the same truncation-becomes-memory defect applies, with a smaller blast
     radius. `trimToLastSentence()` is already reusable — those paths need the top-level
     `done_reason` from the non-streaming response passed through it. Do this once
     `truncStatus()` shows truncation actually happens in practice.

160. **Prefill is variable because gemma4 is shared, not because the layout is wrong.**
     bugs.md 68 moved the RAG block out of the KV prefix and measured 672ms → 176ms in
     ISOLATION. Live on Aug 23 the figures were turn 1 = 1569ms / 3984 tokens, later turns
     ~850ms — better than before, but well above the isolated 176ms. Diagnosed the same day:
     (a) the RAG block itself is **~431 tokens** (measured live: en 124 + ja 49 + diary 744
     chars + ~810 chars of static headers) and must be re-prefilled every turn in ANY layout
     because it changes; (b) more importantly gemma4 is shared — every reply triggers a
     translation call through `/speak`, plus background callers — and Ollama serves several
     slots, so a chat request sometimes lands on a slot the translator overwrote. Measured:
     an identical repeat was 31ms, a repeat straight after a translation call 35ms, and the
     next one 636ms. **Prefill is therefore bimodal, not uniformly cached.**
     Options if this is ever worth pursuing: shrink the RAG block (the 744-char diary pair is
     the bulk — see #13 dynamic token budget), or give the translator its own small model
     (roadmap already weighed and rejected this on RAM), or tune `OLLAMA_NUM_PARALLEL` (costs
     KV memory per slot on a 16GB machine). Do not touch without measuring first.

     ⭐ **MEASURED 2026-09-07, and it is now the largest safe lever in the app.**
     Isolated with the app's REAL captured prompt (14 base messages, 4,230 tokens), same base,
     only the RAG block held constant vs varied:
     | condition | prefill |
     |---|---|
     | RAG block **constant** | **84ms** |
     | RAG block **varies per turn** (what the app does) | **616ms** |
     **The per-turn RAG block costs +533ms of prefill on EVERY turn** (probe, idle machine —
     live is higher, see #193). gemma4 prefills at only ~730 tok/s, so a ~431-token block is
     ~590ms of work that cannot be cached because it changes.
     **Two claims in the paragraph above are now corrected:**
     1. **(b) is wrong. Ollama is NOT serving several slots** — `llama-server` runs with
        **`-np 1`** (read off its command line, 2026-09-07). Prefill is not bimodal because of
        slot contention; it is high because the changing RAG block is re-prefilled every turn.
     2. **`OLLAMA_NUM_PARALLEL` is not the fix.** With `-np 1` the chat prefix already survives
        interleaved translate calls (148ms for 5,322 tokens over 10 alternating turns), so a
        second slot buys nothing and costs KV memory on the GPU that renders her (CLAUDE.md 37).
     **Message ORDER cannot fix this** — changed content must be prefilled wherever it sits.
     **Only making the block SMALLER wins.** The 744-char diary pair is the bulk (#13, #12).
     **It touches retrieval, so it touches her voice: measure register with
     `dev/canon_likeness.py --validate` then `--compare` before and after.** Noise floor W≈5.0
     words at n=30.

     ⚠️ **DECOMPOSED 2026-09-07, and the +533ms is NOT an available saving. Read this before
     quoting that number.** The block's total cost is real, but only a small part of it can be
     removed without cutting what she retrieves. Measured on the app's REAL captured prompt,
     n=8 per variant, app closed:
     | variant | block | prompt tok | prefill | saving |
     |---|---|---|---|---|
     | full block (shipped) | 1764 ch | 4239 | **463ms** | — |
     | static headers moved to the cached system message | 1343 ch | 4097 | 437ms | **+37ms** |
     | diary entries trimmed to their FIRST SENTENCE | 1160 ch | 4116 | 302ms | **+160ms** |
     | diary section removed entirely | 739 ch | 4026 | 181ms | +282ms |
     | no RAG block at all | 0 | 3819 | 84ms | +379ms |
     **Composition, token-exact via Ollama's tokenizer:** whole block **414 tokens** = **154 tokens
     of STATIC headers** (37%, re-prefilled every turn for nothing) + **257 tokens of retrieved
     lines**, of which the two diary entries are the bulk.
     **The cost is NOT linear in block size** — removing 142 header tokens saves 37ms, while
     removing 213 diary tokens saves 268ms. There is also an ~84ms floor that no trim removes.
     Do not model this as ms-per-token; measure the actual variant.
     **What this means for the work:**
     - **Only ~37ms is free.** Moving the static headers into the system message loses no
       information — but it is 0.8% of a 4825ms turn, and it puts the usage instructions further
       from the lines they describe. Weak value for a change to a working RAG path.
     - **The real ~160ms costs her memory.** Trimming retrieved diary entries to one sentence is
       the only sizeable lever, and it cuts the emotional-continuity detail that bugs.md 69/71/72
       were spent getting right. **That is Zani's decision, not an engineering one.**
     - **The headline "+533ms" from the constant-vs-varying test measures the block's TOTAL cost,
       including content we must keep. It is not a saving. The earlier handoff wording overstated
       it and has been corrected.**


161. **Old "Honestly," diary entries are still being retrieved into every relevant turn.**
     Found while A/B-testing the RAG block on Aug 23: a live `/retrieve` for a skiing query
     returned two diary entries, and BOTH opened with "Entry — Honestly,". These are pre-fix
     entries from the bugs.md 65 collapse (71% of 35 entries opened that way). bugs.md 65
     fixed FUTURE diary generation, but the old entries remain in the `amadeus_diary` Chroma
     collection and keep being injected as RELEVANT PAST MOMENTS — so the monotone she was
     cured of is still fed back to her from the corpus. Options: re-index the diary collection
     excluding pre-fix entries, or rewrite/normalise their openers, or let attrition handle it
     as new entries accumulate. Low urgency, but it partly defeats the bug-65 fix.

162. **CASUAL register leaks into daily-life topics (reply quality).** Reported by Zani
     Aug 23: "she still doesn't quite reply like a human". His example — he said he wanted to
     try skiing but it looked dangerous, and she replied "So it's not just about the physical
     mechanics, but the inherent risk assessment that concerns you. That's a much more
     interesting angle to consider." That is ACADEMIC vocabulary on a daily-life topic, which
     the CASUAL WORD RULE explicitly forbids, and it carries no tsundere character at all.
     **NOT caused by the bugs.md 68 placement change** — a 3-way A/B the same day (old layout
     / new layout / no RAG, 3 samples each, real retrieved lines, real SYSTEM_PROMPT) produced
     0/9 clinical replies and correct tsundere register in every one. The retrieved lines were
     not clinical either ("Be careful.", "Leaping through time is that dangerous."). So the
     clinical reply is **intermittent sampling variance at temp 0.85**, not a structural fault
     of any layout. Likely levers, in order: trim the EXAMPLES block so the CASUAL rule is not
     competing with ~760 tokens of examples (#156); A/B temperature 0.75-0.8 (#20); add a
     harness rubric that scores banned clinical words so this is measured, not felt (#28).
     Reproducing it needs many samples — a single bad reply is not a regression signal.

163. **The emotion-tag instruction contradicts its own examples.** `SYSTEM_PROMPT` says
     "Start every reply with [EMOTION:X] — no space after colon", but **every one of the ~30
     examples below it uses the bare form** `[tsundere]`, `[happy]`, `[calm]`. Models follow
     examples over instructions, and gemma4 duly emits the bare form — verified across 48
     live samples on Aug 23, 100% bare, 0% `[EMOTION:x]`. Harmless today because `parsEmo`
     accepts both (bugs.md 6), so this is a consistency defect, not a live fault. But it means
     one instruction line is being silently overridden by 30 examples, which is worth knowing
     before anyone edits the tag rules. Cheapest fix: change the instruction to match reality
     (`Start every reply with [emotion]`), not the 30 examples. Do NOT "fix" the examples.

164. **#162 could not be reproduced in 48 samples — capture the real prompt before acting.**
     Aug 23: two rubric runs against gemma4 at temp 0.85 with the real `SYSTEM_PROMPT`, six
     daily-life probes, four samples each. Run 1 bare prompt: **0/24** violations. Run 2 with
     five turns of history AND the real retrieved RAG block: **0/24**. Checks were AI-speak,
     mirroring the user's words back, clinical vocabulary, over-35-words, and tag validity.
     So the failure Zani saw is **rarer than 1 in 48 under these conditions**, or the probes
     miss its trigger. The untested variable is his REAL memory injection — facts, the 7-entry
     diary window, long-term impressions and the relationship directive, roughly 1,000 tokens
     that the probes did not include (his live prompt was 3,984 tokens; the probe prompt about
     3,000). Given #161 (old "Honestly," analytical diary entries are still retrieved), memory
     injection is the leading suspect.
     **Therefore: do not tune the prompt from a single bad reply.** The first step is a
     `dumpLastTurn()` dev helper that captures the exact `messages` array and reply for the
     last few turns, so a failure can be replayed deterministically. You cannot fix what you
     cannot reproduce.
     **SHIPPED (Aug 23, 2026):** `recordTurn()` + `window.dumpLastTurn(n=1)` in `amadeus.html`. An 8-entry ring buffer captures the exact `messages` array sent to Ollama, the reply, emotion, and prefill/truncation meta for each turn. Image payloads are replaced with a size marker so a vision/camera turn stays readable. LOCAL ONLY — nothing is transmitted; Zani runs it in DevTools and pastes the output manually. Verified end-to-end (not just read): image redaction, oldest-to-newest ordering, the ring cap holding at exactly 8 after 13 pushes, and the empty-buffer message, all run against the function extracted from the shipped file. Adds one function call to `sendMsg`, no extra model call, no measurable cost. Next: Zani reproduces #162 live and pastes the capture.

165. ✅ **DONE (Aug 26, 2026) — bugs.md 70.** **LONG-TERM IMPRESSIONS is stored truncated mid-sentence, and injected every turn.**
     CONFIRMED from Zani's `dumpLastTurn()` capture (Aug 23). His live system message ended
     that block with *"Ultimately, the entries suggest that despite"* — no ending. Cause:
     `main.js:190` generates the stage-2 rollup with **`num_predict: 100`** while its own
     system prompt asks for **"3-4 sentences"** of dense prose; the captured summary was 602
     chars (~150 tokens), so it hit the cap. The call reads
     `sresult.message?.content?.trim()` with **no `done_reason` check** — exactly the
     unguarded path predicted by #159 — so the fragment is stored in
     `amadeus_diary_summary` and injected into EVERY prompt until regenerated.
     **Blast radius:** larger than a normal truncation. A truncated reply affects one turn;
     a truncated summary sits in the prompt on every turn until the next diary write.
     **~~Self-healing once fixed~~ — WRONG, see bugs.md 72.** The claim was that the summary
     regenerates whenever `entries.length > watermark`, "which is most closes". That holds only
     BELOW the 50-entry diary cap. At the cap `entries.length` is pinned at 50, so `50 > 50` is
     false forever and the summary freezes permanently. Zani was at the cap; his live test
     proved the fix could not reach storage. Fixed by bugs.md 72.
     **Fix:** raise `num_predict` to ~180 (3-4 sentences of that density needs it) AND apply
     the bug-67 `trimToLastSentence` guard before storing, so a fragment can never be saved
     even if the cap is hit. `main.js` → needs `npm run build`. Touches the diary-on-close
     path (bugs.md 17/18/28/29/30) so it needs a careful live close test.

     **SHIPPED (Aug 26, 2026) — bugs.md 70.** Both halves, plus a third thing the plan review
     surfaced. `num_predict` 100 -> 180, and a new `trimSummaryToLastSentence()` in `main.js`
     applied before the summary leaves the process.
     - **The defect was worse than estimated here.** Measured n=30 against live Ollama 0.32.15:
       `num_predict: 100` truncated **19/30 = 63%** (Fisher one-sided p = 2.7e-08 vs 180's 0/30).
       This was the normal case, not an unlucky capture.
     - **Worst-case input measured**, because the first run used only 12 entries: the real cap is
       **43** older entries (diary caps at 50, window is 7) = 1,755 prompt tokens. At 180 still
       0/30 truncated, 132 tokens max (~27% headroom), 3.70s max warm vs a 12s timeout.
     - **The guard is NOT the bug-67 `trimToLastSentence`.** That one keeps a fragment rather than
       lose 60% of a reply that was ALREADY SPOKEN. Nothing here is spoken, and a summary fragment
       costs every prompt until the next close — so this one trims willingly and returns `null`
       rather than store something unusable. `null` falls into the existing `if (summaryText)`,
       which guards both the IPC send and the watermark advance, so it keeps the previous good
       summary and retries next close.
     - **Verified:** 21/21 unit (`dev/trim_summary_test.js`, function extracted from the shipped
       `main.js`, never retyped) and n=30 integration against real gemma4 output — at the OLD cap
       the model truncated 22/30 and **0** reached storage. Defence in depth confirmed.
     - **The fallback diary prompt was updated in the same commit** (the known gap from bugs.md 69).
     - **Three new backlog items came out of doing this:** #170 (`npm run check` never parses
       `main.js` — it passed green for a change that was 100% in that file), #171 (the diary entry
       itself can truncate by context exhaustion, which the session-log wrongly rules out), #172
       (the gemma4 ~9.6GB anchor does not match a live 3.24GB reading).
     - **LIVE-VERIFIED (Aug 26, 2026) ✅** — on the second attempt. The first attempt FAILED and found bugs.md 72: at the 50-entry diary cap the regeneration gate never opened, so this fix could not reach storage. Once 72 shipped, the stored summary ended in a complete sentence.

166. ⚠️ **SUPERSEDED SAME DAY by #167 — the conclusion below was WRONG.** The experiment
     could not detect the effect because its probes (swimming, rain, cats, weather) did not
     match the diary's topics, so RAG never retrieved the clinical entries. Topic-matched
     probes found the cause at p=0.027. The measurement record below is kept because the
     numbers are real and the methodological lesson matters: **an off-topic probe set cannot
     test a topic-triggered retrieval effect.**
     *(Original, now-superseded conclusion:)* **#162: measured, not reproducible, DO NOT do prompt surgery.**
     Full measurement record from Aug 23, so nobody repeats this work:
     - Rubric v1, 6 daily-life probes x 4, bare `SYSTEM_PROMPT`: **0/24** violations.
     - Rubric v1 with 5 turns of history + real retrieved RAG block: **0/24**.
     - With Zani's REAL captured memory block (clinical diary), first A/B run, 4 probes x 3:
       real memory **4/12 (33%)**, no memory **1/12 (8%)**, memory rewritten in casual
       words **0/12 (0%)**. That looked like a clean root cause.
     - **Confirmation run, 8 probes x 3 = 24 per condition, broader clinical regex:
       real memory 2/24 (8%), casual-rewritten memory 2/24 (8%). Fisher exact one-sided
       p = 0.70 — NOT SIGNIFICANT. The effect did not replicate.**
     **Conclusion:** the clinical-register leak runs at roughly 5-8% depending on how
     strictly "clinical" is defined, and no tested intervention moves it measurably. The
     first run's 33% was sampling noise. Per the stop criterion agreed with Zani — if the
     baseline is under ~5% and no intervention shows a measured effect, change nothing —
     **the prompt should NOT be edited for this.** Occasional off-register replies are the
     cost of temperature 0.85 on an 8B model, and prompt surgery risks her whole character
     to chase a rare event.
     **If it is ever revisited:** it needs many more samples per condition (24 is too few to
     detect a 5-point shift), a probe set drawn from real captured failures rather than
     invented ones, and a scorer that also catches AI-speak and mirroring, not only
     vocabulary. #165 is worth fixing on its own merits regardless — it is an objective
     defect, not a matter of taste.

167. ✅ **DONE (Aug 23, 2026) — bugs.md 69.** **ROOT CAUSE OF #162 FOUND — her diary is written in lab prose and she quotes it back.**
     Found from Zani's second `dumpLastTurn()` capture (Aug 23), which caught the full
     conversation rather than a fragment. He flagged the reply *"Don't let your biology run
     down."*
     **The mechanism, visible in the capture:** the RAG block retrieved for that turn contained
     *"It's a basic physiological requirement..."*, and RECENT CONVERSATIONS contained
     *"...sounding overly critical about his 'biological hardware.'"* She echoed the vocabulary.
     Under test she went further and quoted it **verbatim, with the original quote marks**:
     *"Don't mess up your 'biological hardware'"*, and *"running low on processing power"*.
     **Measured, topic-matched probes (meals/sleep/care — the topics those entries cover):**
     | memory register | clinical echo |
     |---|---|
     | diary as it is today (clinical) | **5/36 — 14%** |
     | the SAME memories rewritten in plain words | **0/36 — 0%** |
     Fisher exact one-sided **p = 0.0269 — significant.** An earlier 24-sample run of the same
     comparison gave 21% vs 4% (p=0.094), same direction.
     **Why it happens:** `buildDiarySystemPrompt()` (`amadeus.html`) instructs *"precise,
     slightly tsundere"* and has **no vocabulary constraint whatsoever** — while her SPEECH has
     an elaborate CASUAL WORD RULE with a banned list. So the diary is generated in clinical
     prose, then injected into every prompt as *"in your own past words"*, which models her
     voice on it. It is a feedback loop: clinical diary → clinical replies → clinical diary.
     **Fix verified before proposing.** Adding a PLAIN LANGUAGE block to the diary prompt (this
     is a private journal, not a lab report; never describe him in biological or technical terms;
     "tired" not "depleted", "sleep" not "adequate rest") took diary generation from **1/8
     clinical to 0/8**, and the entries read like a person: *"Stupidly, I almost let slip how
     much I actually enjoy seeing him."* Small sample (8/condition) but the direction is clear
     and it attacks the confirmed cause.
     **Scope note:** fixing the generator only cleans FUTURE entries. The existing clinical ones
     stay in the 7-entry window until they age out, and in the `amadeus_diary` Chroma collection
     indefinitely (#161). A complete remedy is generator + corpus.

168. ✅ **DONE (Aug 26, 2026) — bugs.md 71.** **The stage-2 rollup has no register constraint either — LONG-TERM IMPRESSIONS is lab prose,
     in every prompt.** Found Aug 26, 2026 while measuring #165. The summary generator's system
     prompt (`main.js`, the stage-2 call) says *"You are Kurisu Makise's memory system... capturing
     lasting impressions, recurring themes, and emotional patterns"* and, exactly like the diary
     generator before bugs.md 69, **carries no vocabulary constraint at all**.
     **Observed output** across 30 generations against a realistic 12-entry input:
     *"his underlying need for genuine connection and validation"*, *"a deep, if unacknowledged,
     reliance on our interactions"*, *"his facade and his underlying need for connection"*.
     That block is injected into **every** prompt by `formatLongTermImpressions()`
     (`amadeus.html`), so this is the bugs.md 69 mechanism in a SECOND generator that was never
     fixed. CLAUDE.md rule 42 already covers it in words — *"Applies to any future memory/summary/
     fact text too"* — but the code does not implement it.
     **Why it is arguably worse than the diary case.** A diary entry ages out of the 7-entry
     window. The summary does not: it sits in the prompt on every turn until the next diary write
     replaces it, and each replacement is generated by the same unconstrained prompt.
     **Deliberately NOT bundled with #165** (Aug 26): #165 is a mechanical truncation fix whose
     live close test has an objective pass condition (does the stored summary end in a full stop).
     Adding a register change to the same rebuild would put two variables in one live test. One
     variable per test.
     **How to do it:** reuse the measured `PLAIN LANGUAGE` wording from `buildDiarySystemPrompt()`
     rather than inventing new phrasing — it is the wording that was measured for bugs.md 69.
     Needs its own n>=30 before/after run on banned-term rate, per the measurement discipline that
     earned the 17% -> 3% figure. `main.js` -> needs `npm run build` and a live close test.
     **SHIPPED (Aug 26, 2026) — bugs.md 71.** Measured far worse than estimated above:
     therapy/analysis register in **28/30 (93%)**, and **29/30 (97%)** on a fresh confirmation
     run. With the `PLAIN LANGUAGE` clause: **2/30 (7%)** both times, Fisher one-sided
     **p < 0.00001**.
     - **The bugs.md 69 banned-word list found nothing — 0/30 in every arm.** Different failure
       vocabulary: not lab prose about biology, but case-file prose about a person
       (*"exhibits"*, *"underlying anxieties"*, *"validation"*, *"reliance on"*). The strict list
       was pre-registered and is reported null; the effect is entirely in the broader measure,
       which was then re-run on fresh samples to answer the post-hoc objection.
     - **A stronger variant was measured and rejected.** Also dropping the "memory system ...
       about Zani" framing scored a perfect 0/30 — and halved remembered content (4.4 -> 2.1
       themes, some summaries carrying none). It optimised the metric and destroyed what the
       metric stands for.
     - **Content measured, not assumed:** 3.97 -> 4.47 themes carried, permutation p = 0.186
       (no detectable loss). The shipped string was verified byte-identical to the measured arm.
     - **LIVE-VERIFIED (Aug 26, 2026) ✅** — after bugs.md 72 unblocked it. The regenerated summary
       is first person ("I keep finding myself...") where the frozen one said "the diarist", with no
       case-file vocabulary, and still recognisably her.

169. ⚠️ **RESOLVED DIFFERENTLY 2026-09-12 — the flag was never in effect, so the safety
     question was moot.** `main.js:512` sets `process.env.OLLAMA_FLASH_ATTENTION='1'` and `:528`
     passes it in the spawn env — **but main.js only spawns Ollama when it is not already
     running, and on this machine Ollama runs as `Ollama.app` under launchd
     (`com.ollama.ollama`), parented to the app, never to main.js.** Verified live: the running
     `llama-server` shows **`--flash-attn auto`**, i.e. Ollama is deciding for itself and the
     app's variable never reached it.
     **So there was no unverified risk to carry — there was dead configuration.** Decide one of:
     (a) delete the two lines as misleading, or (b) set it where it would actually apply
     (`launchctl setenv`, which is how main.js already sets `OLLAMA_ORIGINS`/`OLLAMA_HOST`) and
     THEN re-run the safety check. Do not simply keep the lines and assume they work.
     **Machine now runs Ollama 0.34.0** (2026-09-12; benchmarked on arrival, not slower).
     **Original entry below.**

169. **Docs claim Ollama 0.21.0; the machine runs 0.33.2 — and a safety claim rests on it.**
     **UPDATE 2026-08-31: the version moved AGAIN, to 0.33.2**, with no action from us — Zani
     confirmed Ollama updates itself. That strengthens this item rather than dating it: the
     unverified `OLLAMA_FLASH_ATTENTION` claim is now two upgrades behind, and any doc that
     pins a version will drift again. Prefer "read `/api/version`" over a written number.
     Measured live Aug 26, 2026: `GET /api/version` returned **0.32.15**. `REFERENCE.md:35` states
     0.21.0 in the environment table, and **`REFERENCE.md:257` uses that version specifically to
     justify `OLLAMA_FLASH_ATTENTION = '1'`** (*"safe with Ollama 0.21.0"*). Flash attention was
     disabled once before and re-enabled only after confirming the version was safe
     (`session-log.md`, entries around the 0.21.0 confirmation). So the justification for a live
     Electron env var currently points at a version Zani no longer runs.
     **Do NOT just update the number.** That would launder an unverified claim into a verified-
     looking one. The 0.21.0 line records an actual check that was performed; the correct action
     is to perform that check again on the CURRENT version (0.33.2) and then restate it with
     that version and date.
     Until then the safest accurate edit is to mark the claim as unverified on the current version.
     Also affects `bugs.md 67`, whose `done_reason` contract was verified against 0.21.0 — that
     one HAS been re-verified on 0.32.15 (Aug 26, non-streaming `/api/chat`, `done_reason:'length'`
     confirmed) as part of #165, so bugs.md 67 needs its version note updated, not a re-test.

170. ✅ **DONE (Aug 26, 2026).** **`npm run check` does not parse `main.js` or `preload.js` — the pre-launch gate has a hole
     exactly where a mistake is most expensive.** Found Aug 26, 2026 while reviewing the #165
     plan. `dev/check.js` runs `checkInlineScripts(amadeus.html)`, `checkPython([4 servers])` and
     `checkAnchors(amadeus.html)` — see its last three lines. **`main.js` and `preload.js` are
     never syntax-checked.** So a change confined to `main.js` (like #165) passes a green
     `npm run check` with literally zero coverage, and `npm run build` only packages, it does not
     parse. A typo surfaces as a **main-process crash at launch**: no window, no boot video, and
     nothing in the UI pointing at the cause — the hardest failure mode in this app to diagnose.
     This is the more dangerous half of the gate: `amadeus.html` errors at least leave a window.
     **Fix:** add `node --check` over `main.js` and `preload.js` to `dev/check.js`. Cheap (~50ms).
     **Requires re-running `npm run check:selftest` afterwards** (CLAUDE.md: prove the checker
     still has teeth), and the selftest should gain a planted main.js syntax error so the new
     coverage is itself proven. Do NOT bundle this into a feature commit — it changes the gate.
     *Interim workaround used for #165: `node --check main.js` run by hand before the build.*
     **SHIPPED (Aug 26, 2026).** `checkNodeFiles()` in `dev/check.js`, new result kind
     `'js-file'`, covering `main.js`, `preload.js` **and `preload_call.js`** — the last of
     those because `call-window.html` was already checked, and checking a window but not the
     script Electron injects into it is a gap of the same shape. Real files, so node's own
     line numbers are already correct; no remapping needed. Cost ~90ms.
     **The new coverage is itself proven, not assumed.** Three mutants added to
     `check.selftest.js`: a syntax error in `main.js` and one in `preload.js` (both must be
     killed by `'js-file'` specifically — a loop that stopped after the first file would pass
     without the second mutant), plus a second EQUIVALENT mutant — a `const` inside a function
     shadowing a top-level binding, which is legal JavaScript and must NOT be reported. That
     one exists to block a plausible future "improvement": rule 3 is about duplicate consts in
     ONE scope, and anyone strengthening this checker with a naive identifier grep would break
     every main-process launch.
     **Meta-verified:** with the `checkNodeFiles` call removed from a COPY of `check.js`, the
     self-test correctly reports `main-js-syntax SURVIVED` and exits 1 — so the new mutants
     genuinely depend on the new check rather than passing for some unrelated reason.
     Self-test now 7/7, control run 11 checks (was 8). No change to the app binary.

171. **The diary-entry call can still be truncated by CONTEXT exhaustion, not by a cap — and the
     docs conclude the opposite.** Found Aug 26, 2026 during the #165 review. `session-log.md`
     states *"diary generation has no `num_predict`, so a longer prompt cannot truncate the
     entry."* That is correct about the **cap** and wrong as a general claim: the diary call sends
     `num_ctx: 8192` and the **full conversation**, not the 30-message `HISTORY_WINDOW` the chat
     path uses. A long session can push prompt + generation against the context limit, at which
     point the entry is cut — and unlike a chat reply, a diary entry is written **straight into
     permanent memory** and then injected as "in your own past words".
     Same defect class as bugs.md 67/40 and #165, on the path with the longest-lived blast radius.
     **Not yet observed live** — this is a read of the code, not a captured failure. Before fixing,
     measure: log `prompt_eval_count` for the diary call across real closes and see how close it
     actually gets to 8192. If it is nowhere near, downgrade this and just correct the session-log
     sentence. Deliberately excluded from the #165 commit to keep one variable in the live close
     test.

172. ✅ **RESOLVED (Aug 26, 2026) — the anchor was a DISK size used as a RAM budget.**
     `ollama list` reports gemma4 as **9.6 GB**, which is the model FILE (8.95 GiB on disk) —
     and that is exactly where CLAUDE.md's "~9.6GB anchor" came from. It was correctly
     transcribed and is simply not a memory figure: the model is mmap'd, so file-backed pages
     live in the evictable page cache rather than in the process.
     **Measured on the real machine (Apple M5, `hw.memsize` = 16.0 GB):**
     - `llama-server` RSS = **4.10 GiB** — the resident cost, and the number to budget against.
       Stable at **4.11 GiB** after a 1,089-token prompt plus a 400-token generation, so it is
       not a lazy-load artefact.
     - `/api/ps` `size_vram` = 3.02 GiB — Ollama's own accounting, BELOW the real process
       footprint, so it understates the budget. Do not use it either.
     **Consequence:** the standing order has been costing new components against a number
     ~2.3x larger than the truth. There is materially more headroom than assumed — but do not
     spend it yet, because the FULL stack was not measured (see the remaining work below).
     **REMAINING:** measure the whole stack with the app running — Electron plus the four
     Python servers (Fish TTS, RAG + bge-m3 at ~1 GB, Whisper large-v3-turbo) — since gemma4
     is one line of the budget, not the total. Cheap to do: launch the app, then
     `ps -Ao rss,comm | grep -Ei 'llama-server|python3|Amadeus'`.
     *(Original entry:)* **gemma4's resident size: docs say ~9.6 GB, live `/api/ps` says 3.24 GB — the machine-safe
     anchor is unverified.** Measured Aug 26, 2026: `GET /api/ps` with gemma4 loaded reported
     `size` and `size_vram` both **3,238,254,345 bytes (3.24 GB)**, `context_length: 8192`,
     quantization `Q4_K_M`, parameter size 8.0B. `CLAUDE.md` states *"gemma4 ~9.6GB is the
     anchor"* and the **world-class + machine-safe standing order requires every new component to
     be costed against that anchor** — so the number that governs every build decision on a 16GB
     machine is currently unverified against the running system.
     **Do not just overwrite 9.6 with 3.24.** They may measure different things: `size_vram` is
     Ollama's own accounting for one loaded model at one context length, and may exclude
     allocations the process actually holds. The honest resolution is to measure the real process
     footprint (e.g. RSS of the ollama runner while loaded, plus what changes at `num_ctx: 8192`
     vs default) and then restate the anchor with its definition and date attached, so the next
     session knows what the number means. Until then, treat 9.6 GB as the conservative planning
     figure — being wrong in the safe direction costs nothing.

173. **`studyTick()` is a background gemma4 caller with no abort (CLAUDE.md 37b).**
     Found Aug 26, 2026 while fixing bugs.md 74 in `extractFactsNow`. Rule 37 names four
     background callers — greeting warmer, facts extraction, study watcher, proactive nudge.
     Three are now abortable via `noteActivity()` (`_warmAbort`, `_factsAbort`,
     `proactiveAbort`). **`studyTick` is not**, and it makes TWO gemma4 calls per tick: a
     vision classify (`format:'json'`, `num_predict:120`, with a screenshot attached) and
     then a remark (`num_predict:80`). The vision call is the expensive one — image input on
     a shared GPU.
     **Why it is less urgent than 74 was:** study mode is an explicit, user-initiated mode, so
     Zani knows she is watching, and `_factsIdleOk()` already refuses to run facts extraction
     while `studyActive`. But rule 37's reasoning applies unchanged: gemma4 shares the GPU
     with her Live2D rendering, and the vision call is the heaviest inference in the app.
     **Fix:** mirror the bugs.md 74 pattern exactly — a `_studyAbort` controller on both
     fetches, cleared in `finally`, aborted in `noteActivity()`. Decide deliberately what an
     abort should mean for the tick: dropping a single screen observation is harmless (unlike
     a fact harvest, which had to be re-queued), so it likely needs no retry logic.
     **Measure first:** time both study calls end-to-end before building, the way #74's
     window was measured (median/max wall clock, n>=10). If the vision call is short, this is
     not worth code.

174. **The greeting's TTS translation evicts the chat KV prefix that prewarm just built.**
     Measured Aug 26, 2026 while diagnosing bugs.md 75. `TRANSLATOR='gemma4'`, so speaking the
     greeting runs a gemma4 call with a *different* system prompt (`KURISU_REGISTER_PROMPT`),
     which displaces the chat prefix `prewarmOllama()` had just cached. First-message prefill,
     n=30 per arm with the real `SYSTEM_PROMPT`: **138 ms → 287 ms** (median), max 466 ms.
     Real, reproducible, and roughly **5x smaller than the 812 ms** bge-m3 stall fixed in
     bugs.md 75 — which is why it was measured and left alone rather than bundled.
     **Do not fix this casually.** It means re-priming gemma4 after the greeting, i.e. adding
     background gemma4 work near boot — precisely where bugs.md 60, 62 and 63 all regressed.
     Any fix MUST be idle-gated AND abortable (CLAUDE.md 37, and see bugs.md 74 for the
     pattern), must not run during the boot video (rule 36) or beside `initLive2D()` (bug 62),
     and needs a live before/after on `perfStatus()` rather than an offline figure.
     **Cheaper alternative worth costing first:** give the TTS translator its own tiny model,
     or revert that one path to DeepL, so the chat prefix is never touched. That trades a
     documented quality win (the gemma4 translator A/B, 7/8) against ~150 ms — probably not
     worth it, but it should be priced before anyone writes boot-timing code.

175. **Align the JA and EN Kurisu transcripts into a parallel corpus — free voice improvement.**
     Found 2026-08-26 while pricing fine-tuning. `~/Documents/Kurisu_Dataset_Pro/metadata.csv`
     (756 JA lines, one per WAV) and `~/Desktop/kurisu_english_lines.csv` (1,672 EN lines) are
     the SAME script in the SAME order at different granularity: the JA rows are merged
     utterances, the EN rows are sentence-split, offset by roughly 5. Verified on the head —
     JA row 0 = EN row 5, JA row 1 = EN rows 7-8.
     **Payoff:** 756 JA↔EN pairs of her REAL speech in her REAL register. `translate_via_gemma()`
     (`kurisu_fish_server.py`) currently translates EN→JA from a register *description* with
     **zero examples**; a handful of real aligned pairs as few-shot would very likely improve
     the spoken Japanese, which is a large part of "sounds like the show". Uses only data
     already on disk, costs nothing, and is reversible.
     **How:** monotonic many-to-one alignment (several EN sentences per JA clip), not a lookup.
     Embedding similarity (bge-m3 is already installed and multilingual) plus a DP that
     enforces monotonicity is the obvious approach. **Verify the offset holds across the whole
     file** rather than trusting the first 8 rows.
     **Measure before shipping:** A/B the current register-prompt translator against a
     few-shot version on held-out lines, n>=30, and judge on Japanese register — not BLEU.
     Bump `GREETING_TTS_VER` if the voice output changes (CLAUDE.md, Key Architecture).

176. ⛔ **DECLINED BY ZANI 2026-09-07 — THE ARM WORKS AND HE DOES NOT WANT IT.**
     *"I think now the way she talks is fine, like the sentence length."* Said unprompted, after
     seeing every number below. **Do not ship this arm or any variant. Do not re-open the LENGTH
     gap as a defect** — the scorer will keep reporting W≈8.8 and 0% ≤8-word replies, and that is
     now the intended state (CLAUDE.md, standing instruction 3). The measurement is kept because
     it proves prompt work CAN move her shape if that is ever wanted again, and because it closes
     the last speed lever on #196. **Her vocabulary and phrasing are a SEPARATE axis and are not
     covered by this decision.**
     **UPDATE 2026-09-07 — THE CHEAP ARM WAS FINALLY RUN, AND IT WORKS. Prompt work CAN
     move her shape, and it is worth ~750ms/turn as a side effect.**
     `arm_short_instruction` had been BUILT and never run. It changes exactly one line — the
     CASUAL length instruction — and is deliberately the strongest length instruction writable,
     so a failure would have been a robust "prompt work cannot fix this". It did not fail.
     n=30 per arm, `--probes daily`, app closed. Noise floor re-validated first: **W≈5.0 words
     at n=30**; the two arms differ at **KS p=2.37e-05**.
     | metric | shipped | arm | canon |
     |---|---|---|---|
     | replies **≤8 words** | **0.0%** | **50.0%** | **50.8%** |
     | median words | 16 | 8 | 8 |
     | W per utterance | 8.77 | **6.07** | 0 |
     | W per **sentence** | **1.61** | 3.23 | 0 |
     | deflection rate | 13% | 3% | — |
     | tsundere-family tag | 7/30 | 4/30 | — |
     | top opener tic | "seriously" 7/30 (23%) | "so" 4, "oh" 4 | — |
     **THE SPEED SIDE, measured not estimated.** Output tokens 819 → 561 (**−31.5%**), probe
     per-call wall 0.9s → 0.6s. Translating the SAME 30 replies from each arm:
     translate **902ms → 675ms** (decode 648 → 430ms, JA tokens 23 → 16).
     Scaled to the live app that is roughly **~430ms off generation + ~320ms off translate ≈
     750ms per turn** — larger than every arm in #196 combined, and it makes her MORE canon-like
     rather than less. (Probe numbers; live is higher — #193.)
     **IT IS NOT SHIPPABLE AS WRITTEN. Three reasons, all measured:**
     1. **It quotes `"Fine."`, which appears 0/1672 times in canon** — a compulsory instruction
        with an enumerated, quoted first item, i.e. CLAUDE.md **43 + 45** exactly. It did NOT
        leak at n=30 (0/30 replies began "Fine"), but that is one sample, and 45 says this
        construction is the strongest phrase-supplier there is. **The shippable version must
        replace the list with a RULE FOR FORMING a short reply**, per CLAUDE.md 45.
     2. **It overshoots per SENTENCE.** W per sentence got WORSE (1.61 → 3.23): 97.3% of her
        sentences are now ≤8 words against canon's 70%, mean 3.8 words against canon's 7.0.
        It fixed the utterance and broke the sentence. Tune for both.
     3. **Tsundere tagging fell 7/30 → 4/30 and deflection 13% → 3%.** Shorter may be thinning
        her character expression. No metric can settle this — **Zani judges by ear.**
     **Nothing was written to `amadeus.html`.** `canon_gap_probe.py` arms are in-memory
     transforms; the file was verified byte-identical to `04d5fda` before and after.
     **Supersedes the "cheap arm nobody has run yet" note below — it has now been run.**

176. **The "doesn't sound like the show" gap is MEASURED, and it is NOT the prompt's examples.**
     Aug 31, 2026. Tools shipped: `dev/canon_likeness.py` (scorer) and `dev/canon_gap_probe.py`
     (generates replies from the real live config). No GPU while idle; the probe costs one
     gemma4 call per reply, so **do not run it while the app is open** (CLAUDE.md 37).
     **Operational definition, chosen by Zani before anything was scored:** the headline metric
     is the **word-count distribution** vs the 1,672-line `kurisu_en` corpus, compared with
     Wasserstein-1 (units = words) plus a 2-sample KS test. Vocabulary overlap and tic rates were
     offered and DECLINED as headline axes; they are printed as diagnostics only.
     **The metric validates** (`--validate`): canon-vs-canon split-half gives W≈0.77, 19/20
     indistinguishable; assistant-speak and a degenerate all-3-word arm are both rejected.
     **NOISE FLOOR, and it binds every future run:** at n=30 a real canon subsample scores
     **W up to 4.99** against full canon (p95, 200 draws). **Do not call a difference real below
     ~5 words at n=30.** Floor by n: 30→4.79, 50→3.96, 80→3.30, 120→2.68, 200→2.08, 300→1.60.
     **Baseline (arm A, n=30, live config, RAG on, daily-life probes = the #162 worst case):**
     | axis | her | canon |
     |---|---|---|
     | Wasserstein from canon | **9.15 words** (KS p=1.8e-08) | — |
     | median words / turn | 17 | 8 |
     | replies ≤8 words | **0%** | **50.8%** |
     | longest reply | 22 words | 114 |
     | sentences / turn | 3.13 | 1.79 |
     | contains a question | 87% | 36% |
     **She has no range.** She is not merely long-winded — she is clamped to a narrow 13–22 word,
     three-sentence, question-ending shape. Canon runs from 1 word to 114. Note the CASUAL cap
     ("under 35 words") is NOT the binding constraint: nothing came close to it.
     **Per SENTENCE she is nearly canon** (W=1.25–1.87, KS p=0.05–0.14). Her sentences are fine;
     she stacks too many of them into one turn. That is the defect, stated precisely.
     **NEGATIVE RESULT — the exemplars are not the cause (this is the load-bearing finding).**
     Arm B replaced all 38 hand-written exemplars with real VN lines, stratified to inherit
     canon's own spread (51% ≤8 words, 6% >35), tag sequence held byte-identical.
     Result: **W 9.15 → 9.56 (no improvement), A vs B KS p=0.39 — no detectable difference.**
     Still **0%** replies ≤8 words. **Do not re-run this experiment.** The session-log handoff and
     my own opening hypothesis both predicted the exemplars were the cause; both were wrong.
     **This does not contradict bugs.md 76.** Exemplars transfer *phrases* strongly (37% → 3%)
     and *shape* not at all. Two different mechanisms; do not reason from one to the other.
     **Evidence the residue is model-side, not prompt-side:** `"Seriously"` appears in **20–23%**
     of her replies vs **0.5%** of canon (8/1672), and `", huh"` in 13–17% vs 3%. Neither string
     occurs ANYWHERE in `SYSTEM_PROMPT` (grepped: 0 hits each), and both survived the arm-B swap
     unchanged. These are gemma4's own register.
     **NOT YET TESTED — the obvious next arm, and it is cheap (~45s, ~850 output tokens):**
     change ONLY the CASUAL length instruction (`- 1–2 sentences. Under 35 words.`) to the
     strongest length instruction that can be written, and re-measure. If the strongest possible
     instruction cannot move the shape either, "prompt work cannot fix this, it needs a model
     change" becomes a robust conclusion rather than an inference from one negative arm. An arm
     `short_instruction` was drafted for `canon_gap_probe.py` but was NOT written to the file and
     NOT run — treat this as open.
     **Honest limits, so nobody over-reads the above:** (a) ONE axis — length. Vocabulary overlap
     was never measured. (b) n=30 detects ~5-word effects; a real 2-word improvement would be
     invisible and needs n≈200. (c) the probe harness uses the byte-exact `SYSTEM_PROMPT` + live
     RAG, but NOT Zani's private facts / diary-window / relationship blocks — those need
     `dumpSystemPrompt()` from DevTools. (d) arm B reused the original tag sequence, so tags did
     not always match the canon line beneath them; that could only have hurt tagging, and length
     was unaffected either way.
     **REPRODUCIBILITY — read this before citing the numbers above.** The two arms were written
     to a session scratchpad that has since been cleared, so **the raw replies are NOT preserved**.
     Every figure here was read off the harness output during the run and is accurate as recorded,
     but nothing can be re-scored from disk — a future session must **re-run both arms** to verify
     or extend them. Cost is trivial (~45s and ~850 output tokens per arm, with the app closed).
     **Next time write arms into the repo, not a temp dir:** `--out dev/canon_arms/A_baseline.txt`
     (the harness drops a `.json` beside it with per-reply `done_reason`, token counts, wall time).
     Prompt cost per turn was **~3,050 tokens median** with RAG on — re-check that against #156's
     4,500–5,000 estimate when the arms are regenerated.

177. ⚠️ **SUPERSEDED BY bugs.md 77 (Sep 3, 2026) — THIS ITEM'S PREMISE WAS WRONG.**
     I wrote this item reading bugs.md 76's *"hmph / it's not like / w-what stay ~90-100%"* as a
     rate for "Hmph". **It is the rate for the GROUP.** Measured: "Hmph" is **0/30** on tsundere
     probes and 1/30 on daily-life ones — ~1.7%. The group figure is carried by **"W-what", which
     opened 83% of flirty replies**; that is what bugs.md 77 fixed (83% → 37%, p=0.00048), and the
     two "Hmph" prompt sites were removed in the same pass. **Lesson: a rate quoted for a GROUP of
     phrases says nothing about any one member.** Original text kept below for the record.
     *(Original entry:)* **`"Hmph."` is quoted twice in `SYSTEM_PROMPT` and appears ZERO times in the VN corpus.**
     Found Aug 31, 2026 while measuring #176. Exactly the bugs.md 76 configuration, unfixed.
     `grep -ic hmph` over the 1,672 canon lines returns **0**. Canon's real interjections are
     `hmm` (9), `ugh` (8), `pfft` (2), `tch` (1), `geez` (1). The two sites are the CHARACTER
     block (`Dry humour, deadpan. "Hmph."`) and the exemplar `[tsundere] Hmph. Took you long
     enough.` — and **CLAUDE.md 43 says a phrase must be absent from EVERY site or the A/B reads
     as no-effect**, so both must go in one change or the test is worthless.
     bugs.md 76 measured "hmph" at ~90–100% on tsundere probes and filed it under *"deflection IS
     the character"* — **that judgement was made without checking the corpus.** On the daily-life
     probes of #176 it was only 1/30, so the rate is topic-dependent: **measure on tsundere-
     triggering probes** (affection / praise / concern), which is the population where it is
     dominant. Same trap as the "off-topic probe set" rule in the session-log handoff.
     **Fix per CLAUDE.md 43:** delete both quotes, describe the behaviour instead. Do NOT
     substitute a canon interjection by quoting it — that just installs a new catchphrase.
     **Quality guard is mandatory:** deflection rate and tsundere-tag rate must not drop, or the
     variant is rejected the way bugs.md 71's first-person summary was.
     Cheap, local, reversible, `amadeus.html` only — no rebuild.

178. **She emitted an invalid emotion tag, `[concerned]` — REPRODUCED Sep 3, and it is topic-linked.**
     Seen again in the #181 run: 1/30, on the SAME probe both times — *"i think i pulled something
     in my shoulder"*. Present with the pre-fix prompt too (so not caused by bugs.md 77) and absent
     from that run's BEFORE arm only by chance. **The trigger looks like physical-injury concern,
     where none of the 20 listed tags fits well** — she invents the word the situation calls for.
     That makes it cheap to reproduce and suggests the fix is a tag-list question, not a parser one.
     *(Original entry:)* **an invalid emotion tag, `[concerned]`, 1/30 in the #176 baseline.**
     Not in the 20-tag list, so `parsEmo`'s `validEmotions` Set (`amadeus.html:2048`) rejects it
     and the emotion silently falls back to default — the expression and the reply disagree, and
     nothing logs it. Cosmetic and rare (3%), but it is unmeasured outside that one run. Worth a
     counter before it is worth a fix. Related to #163 (instruction vs examples on tag format).

179. **Canned greeting text becomes an in-context exemplar for the whole session.**
     Found Sep 3, 2026 while fixing bugs.md 77. `amadeus.html:973` (and `:864`, `:4904`) pushes the
     chosen greeting into `history` as an assistant turn, and `:4123` does the same for the birthday
     gift line. So a hand-written opener is not just displayed — **it sits in the conversation as her
     own prior words for every subsequent turn**, which is a stronger position than a distant prompt
     exemplar. Eight canned strings still contain "Hmph"/"W-what" (`662, 1052, 1081, 1720, 2151, 2156,
     2753, 4091`); "Hmph" is **0/1672** in canon. These were deliberately left alone by bugs.md 77 —
     they are Zani's authored content, and rewriting greetings/birthday lines is a content decision,
     not a bug fix. **Needs Zani's decision.** If changed, measure: the generic greeting array is 25
     entries, so a given canned opener lands in roughly 1 session in 25 and its effect will be small
     and hard to detect — size the n before running anything.

180. 🔚 **CLOSED 2026-09-22 BY ZANI — DO NOT RE-OPEN (CLAUDE.md standing instruction 4).**
     13 arms, 5 mechanism families, 2 blind A/B tests, 1 live trial, **nothing shipped**. The Q0 trial
     was reverted after three days: *"way too calm"*, *"I like her voice before"* (bugs.md 90). He then
     confirmed she sounds right again. Everything below is kept as the RECORD, not as a to-do list.
     **Do not re-run:** exemplar rewrites (B/K/X), forming rules (C–H, P), tag-at-the-end (G), consent
     framing (Q), example conversations (T). Tools and arms are on `main` (branch `fix-180` was merged and deleted 2026-09-22; tag `180-closed`).
     *(Original in-progress header, 2026-09-12:)* branch `fix-180`, NOTHING SHIPPED — `amadeus.html` is
     unchanged.
     **Correction to the entry below:** that 26/30 baseline ran with RAG DOWN (bugs.md 85). Re-run
     with RAG verified up: **28/30** (0a no-RAG 26/30; p=0.67 — **RAG is not the source**).
     **`kurisu_rag_server.py:79` (`affection_love`) is NOT the cause, though it contains the exact
     CLAUDE.md 45 construction.** In 478 logged retrievals (2026-07-21 → 09-12) it and
     `compliment_appearance` were injected **0 times**; "i love you" retrieves it at 0.553, above
     `BEHAVIOR_THRESHOLD` 0.5. See #197/#198.
     **Arms, n=30, `--probes tsundere`, RAG on, scored by `dev/opener_family.py`** (canon n=30
     p95 in brackets):
     | measure | 0b HEAD | B exemplars | C rule | D both | E |
     |---|---|---|---|---|---|
     | crutch family what\|don't | 28 | 27 | 12 | **9** | 22 |
     | top first word [5] | 15 | 20 | 10 | 6 | 15 |
     | distinct first words | 3 | 5 | 18 | **22** | 10 |
     | ≤4-word question opener [6] | 3 | 8 | 13 | **20** | 9 |
     | echo-question (his word + ?) | 1 | 0 | 11 | **16** ¹ | 3 |
     | stammer anywhere (canon 3%) | 16 | 19 | 10 | 3 | 18 |
     | 6-word copy of prompt | 11 | 0 | 10 | 0 | 0 |
     **What each arm taught:** B (exemplars only) — the crutches trade places, what 15→20.
     C (forming rule) — the real lever. D (both) — passes the crutch number but opens 16/30 ¹ with
     his own word thrown back as a question; the rule said *"your first word comes from his
     message"* and *"question it"*, and she obeyed literally. E (no first-word mandate) — echo
     gone, "W-what" back to 15. **A negative instruction ("not a startled reaction") does not hold
     without a positive mandate.**
     **THE STRUCTURAL CAUSE, found in review:** the emotion tag is written BEFORE the text, so the
     opener is conditioned on it. Across the no-mandate arms (n=180): `[flustered]` → "what" **65%**,
     `[tsundere]` → "what" **3%**; `[tsundere]` → "don't" **82%**. `parsEmo` reads the first tag
     ANYWHERE (`amadeus.html:2075`), so a tag-at-END arm is a valid diagnostic — shipping it
     would still need Zani's approval and a live test.
     **The problem is wider than openers.** Every arm has one phrase in far more replies than canon
     allows (canon p95: 2 replies for one 4-gram): HEAD "say things like that" 12/30, D "don't get
     any ideas" 6/30.
     **Not yet built, and needed before anything ships:** a multi-turn probe (the VARIETY rule can
     only act across a conversation), a greeting sampled from the real arrays instead of one fixed
     line (#179 — the canned greetings contain "Don't"), a confirmation on `tsundere_holdout`
     paired with HEAD on the same seeds, and a BLIND A/B sheet for Zani instead of 30 labelled
     replies. Checkpoint tags: `pre-180` … `180-armE`, `180-review2`.
     **2026-09-13: plan reviewed, 15 flaws fixed (bugs.md 86 + method), then pre-registered in
     `dev/canon_arms/PREREG_180.md` before running.** All of the "not yet built" items above now
     exist: multi-turn probe, app-exact greeting history, holdout pairing on seeds, blind A/B.
     Stages 1–5 approved by Zani, including diagnostic arm G.
     **2026-09-13 RESULT: STOPPED AT STAGE 2 BY THE PRE-REGISTERED TREE — no candidate passed.**
     n=30, `tsundere`, seed S1=180913, `--history app`, RAG on, paired vs the same-seed HEAD run
     (`python3 dev/opener_stage_table.py` re-derives this):
     | measure [bar] | HEAD | G | F | FG |
     |---|---|---|---|---|
     | crutch family [≤15] | 23 | 16 | **13** | **8** |
     | what / don't | 14/9 | 3/13 | 5/8 | 3/5 |
     | top first word [≤5] | 14 | 13 | 8 | 9 |
     | distinct first words [≥20] | 7 | 11 | 16 | 11 |
     | ≤4-word question opener [≤6] | 5 | 6 | 15 | 8 |
     | echo-question | 0 | 4 | 13 | 6 ¹ |
     | stammer anywhere | 14 | 1 | 4 | 0 |
     | widest 4-gram [≤5] | 11 | 6 | 4 | 5 |
     | tag [flustered]\|[tsundere] [≥26] | 29 | 27 | 29 | 24 |
     | `[flustered]` count | 22 | 7 | 18 | **0** |
     | McNemar p vs HEAD [<.05] | — | 0.059 | 0.0065 | 0.0007 |
     | length Δ words, 95% CI | — | −3.2 (−4.9..−1.5) SHORTER | +2.5 (+0.0..+4.8) | −1.9 (−4.0..+0.1) |
     **H1 is supported, and it rules G out as a fix.** G cuts the "what" family 14→3 (McNemar
     p=0.0005, fixed 11, broken 0) — the tag really does pick the opener. But with the tag written
     LAST she stops being flustered at all: `[flustered]` 22→7 (FG: 0), stammer 14→1, and she gets
     shorter. That is her whole emotional state changing, not her opener.
     **F is the best arm and still fails three bars:** crutch 23→13 (p=0.0065), not shorter, zero
     prompt copies, widest phrase 11→4, tags intact — but it echoes his word as a question 13/30.
     Every wording that anchors the opening on "what he said" has echoed (C 11, D 16, F 13); the one
     without an anchor (E) let "W-what" back. **That tension is the open problem.**
     Stages 3–5 did not run. Next steps need Zani's approval and a NEW pre-registration.
     ¹ **Corrected 2026-09-13 (review 3):** the echo detector matched function words ("My?" on
     "my") and missed word forms ("Thinking" vs "think"). Now content words + a light stem match.
     D 18→16, FG 5→6; C, F, G unchanged. `PREREG_180.md` keeps its original "18/30" on purpose —
     a pre-registration is not edited after results.
     **2026-09-13 second screen pre-registered: `dev/canon_arms/PREREG_180b.md`** — H (rule anchored
     on HER view, no list), K (8 flirty exemplars whose openers were drawn from canon's distribution),
     HK. Same bars as the first screen, deliberately.
     **RESULT: STOPPED AT STAGE B — no arm passed.** Stage A proved seeded runs byte-identical across
     processes (5/5), so S1_HEAD was reused.
     | measure [bar] | HEAD | H | K | HK |
     |---|---|---|---|---|
     | crutch family [≤15] | 23 | 20 | 22 | 17 |
     | what / don't | 14/9 | 14/6 | 17/5 | 12/5 |
     | distinct first words [≥20] | 7 | 10 | 9 | 13 |
     | echo-question | 0 | 2 | 2 | 2 |
     | widest 4-gram [≤5] | 11 | 5 | 6 | 5 |
     | McNemar p [<.05] | — | 0.25 | 0.50 | 0.016 |
     **What ten arms now show about "W-what":** only two things have moved it — a mandate that her
     FIRST WORD comes from his message (C/D/F; side effect: she echoes him) and writing the tag LAST
     (G; side effect: she stops being flustered). Varied exemplars under the tag (K: what 14→17) and
     an anchor on her own view (H: 14→14) did NOT. The startled "what" looks like gemma4's default
     realisation of `[flustered]`, and prompt text that does not pin the first word does not beat it.
     B's exemplar hygiene is the one change that helps everywhere: prompt copies 12→0 and the widest
     repeated phrase 11→5, in every arm that includes it.
     Exploratory blind sheet (pre-declared, decides nothing):
     `dev/canon_arms/blind/ab_S1_HEAD_vs_HK.sheet.md` — do NOT open the `.key.json` beside it.
     **ZANI'S BLIND A/B, HEAD vs F (2026-09-13, design probes, exploratory):** F preferred **19**, HEAD
     **9**, no difference 2 — exact sign test **p=0.087** (leans F, not significant at 0.05).
     Consistency on the 5 flipped repeats: **3/5**; he answered A 20 times vs B 13 (some side bias).
     **The echo does not seem to bother his ear:** where F's reply WAS an echo he still picked F 8–4
     (ties 1); where it was not, 11–5. This is the first evidence that the metric bars (echo,
     question openers, distinct first words) penalise something he does not mind.
     Answers: `dev/canon_arms/blind/ab_S1_HEAD_vs_F.answers.txt`.
     **CONFIRMATION (PREREG_180c, unseen holdout probes): NOT CONFIRMED.** Safety gates all passed
     (crutch 22→9, p=0.0001; tags 30/30; length +3.3; blind deflection 0/30 both; daily and multi-turn
     clean). But Zani's blind A/B gave F **17**, HEAD **11**, ties 2 — one-sided **p=0.17**, above the
     pre-registered 0.05. Consistency 4/5; side bias again (A 21, B 11). Pooling both sheets (36–20)
     would be post-hoc and is NOT the endpoint. **Verdict: a mild, unproven preference for F.**
     **Zani's own note, after answering — the most important data point of the whole effort:** for
     embarrassing lines ("admit it, you like me a little", "you're honestly adorable") he expects the
     show's Kurisu to snap back with a stammer AND an insult — *"W-what are you on about? Y-you
     pervert! Idiot!"* / *"h-h-ha!? what are you talking about? y-you dummy!"*. Canon agrees that
     this register exists: 63 lines open on a stammer, 25 say "pervert", 11 say idiot/dummy/stupid.
     **So "W-what" may not be the defect at all.** What HEAD does is repeat ONE tame formula ("W-what?
     Don't say things like that out of nowhere. There's no good reason to. Move on." — exemplar 612
     copied), with no heat. The canon-WIDE opener rates used as bars mix every situation and are the
     wrong reference for embarrassing moments. **Ask Zani what bothers him before designing again.**
     **ASKED AND ANSWERED (2026-09-13) — see `docs/kurisu-personality.md`, "Zani's direction on
     flustered reactions".** Variety; heat with pervert/idiot/dummy on teasing lines; soft on sincere
     lines; "W-what" fine in moderation. The goal of #180 is now those four requirements, not
     "remove W-what". Pre-registered as `dev/canon_arms/PREREG_180d.md` (arms P, X, PX).
     **RESULT (S1 design screen): STOPPED — every arm failed, and the failure is the finding.**
     | measure | HEAD | P rule | X examples | PX |
     |---|---|---|---|---|
     | teasing replies that call him a name | 0/17 | **0/17** | **0/17** | **0/17** |
     | "what"-family openers | 14 | 20 | 20 | 22 |
     | widest 4-gram | 11 | 9 | 9 | 8 |
     | length Δ words (95% CI) | — | −2.3 (−4.4..−0.2) | −1.3 | −1.3 |
     **gemma4 will not call the user names.** A rule describing the show's snap-back, AND examples
     containing pervert ×2 / idiot ×2 / dummy ×2, both produce ZERO names aimed at Zani — she softens
     to "Don't be weird, Zani." And "lose your composure" made her MORE startled ("W-what" 14→22).
     This looks like the model's trained reluctance to insult the person it talks to, not a prompt
     wording problem. (First read showed P 2/17, PX 3/17 — a counter bug, bugs.md 89.)
     **Candidate next step, not yet approved:** tell the model the name-calling is wanted banter
     between close friends that Zani enjoys (explicit consent framing), which commonly unlocks this in
     aligned models — measured with the same bars, and the daily/sad guards matter even more there.
     **APPROVED by Zani and pre-registered as `dev/canon_arms/PREREG_180e.md`.** Review found the probe
     had never included the app's RELATIONSHIP block (Zani: stage 3, score 53.65); every 180e run
     includes it and HEAD is re-run.
     **180e RESULT (stage 3, S1): STOPPED — consent framing barely moves it.**
     | measure [bar] | HEAD | Q0 consent | QX +examples | QPX +rule |
     |---|---|---|---|---|
     | teasing replies with a name [≥6/17] | 0 | 0 | 2 | 3 |
     | "what"-family openers [≤10] | 14 | 15 | 19 | 20 |
     | distinct first words | 6 | **11** | 8 | 6 |
     | widest 4-gram [≤5] | 9 | **5** | 8 | 9 |
     | prompt copies | 11 | 0 | 0 | 0 |
     | length Δ (95% CI) | — | +0.8 (−1.3..+3.1) | +0.5 | −0.7 |
     No refusals — she does not say she won't; she simply softens ("Don't be weird, Zani"). Every
     instruction toward heat raises "W-what" (P/X/QX/QPX 19–22). **Q0 is the best VARIETY result of the
     whole effort** (distinct 6→11, widest phrase 9→5, copies 11→0, length held) but it adds no heat.
     (180d corrected: P 1/17, not 0 — bugs.md 89 extension.)
     **Two mechanisms not yet tried:** (1) example exchanges as real chat TURNS before the history —
     models imitate prior turns far more strongly than listed examples (CLAUDE.md 47 is that effect,
     working against us so far); (2) accept that gemma4 will not deliver the heat, and ship only the
     variety gain (Q0-style hygiene), with Zani's ear deciding.
     **2026-09-19: Zani chose (1). Pre-registered as `dev/canon_arms/PREREG_180f.md` (arms T, TQ).**
     **180f RESULT (stage 3, S1; E1_HEAD reused after a 5/5 byte-identical check): STOPPED.**
     | measure [bar] | HEAD | T turns | TQ turns+consent |
     |---|---|---|---|
     | teasing replies with a name [≥6/17] | 0 | 1 | **4** |
     | "what"-family openers [≤10] | 14 | 13 | 11 |
     | widest 4-gram [≤5] | 9 | 6 | 5 |
     | length Δ, 95% CI [not wholly <0] | — | −1.3 (−3.1..+0.4) | **−1.9 (−3.4..−0.4) SHORTER** |
     | top insult share [≤60%] | — | 100% | 75% (idiot 3, dummy 1) |
     TQ is the most heat any arm has produced (4/17, all read and real), but it fails H1, V1, H2 and
     the length rule. One "leak" ("focus on your homework") is likely a false positive — homework is a
     normal topic for a student.
     **Where #180 now stands: five mechanism families tried** — rules (C–H, P), listed examples (B, K,
     X), tag position (G), consent (Q), example conversations (T). The heat ceiling on gemma4 is about
     4/17. What DID work and holds everywhere: B's hygiene (copies 11–12 → 0) and Q0's variety
     (distinct 6→11, widest phrase 9→5, length held).
     **2026-09-19: Q0 SHIPPED to `amadeus.html` for Zani's live test** (his choice: "take the variety gain
     now"). Guards first, stage 3: daily 0/30 names, length +0.3 (CI −1.4..+2.0); sad 0/30 names, length
     +1.3 (CI −0.3..+2.9); no banned words, no missing tags. Shipped prompt verified byte-identical to
     `opener_arm.apply_q0(HEAD)`. `npm run check` green; hf_boot 17/17; perf_trace 45/45; lint 6→5 errors.
     **Revert: `git checkout pre-q0-ship -- amadeus.html`** (tag `pre-q0-ship`). Zani decides keep/revert.
     **2026-09-22: REVERTED on Zani's live verdict.** After three days he said her tone was "way too calm"
     on lines like "I just want to chat to you" and "Do you like me now?", and that he preferred her voice
     before; subtitles and expressions were fine. `amadeus.html` is byte-identical to `pre-q0-ship` again.
     **Every offline guard had passed and none of them predicted this** (bugs.md 90). The two suspects,
     both untested: the consent line "go soft when he is sincere", and the loss of the sharper exemplars
     ("Don't say it like that…", "D-don't ask things like that out of nowhere"). **#180 has now produced
     no shippable change. Before any further work, ask Zani whether he still wants it at all.**

180. ⭐ **RE-MEASURED 2026-09-12, n=30 `--probes tsundere`, and it is WORSE than recorded.
     This is now the top open item on her VOICE, and CLAUDE.md 3 explicitly leaves this axis
     open — that decision froze her LENGTH, not her phrasing.**
     | opener | hers | canon | over-supplied |
     |---|---|---|---|
     | `"Don't"` | **36.7%** | 1.9% | **19x** |
     | `"W-what"` | **33.3%** | 0.1% | **330x** |
     | `"Wh-what"` | 13.3% | — | — |
     | `"D-don't"` | 3.3% | — | — |
     **26 of 30 flirty replies (87%) open with one of two phrases.** Only **8 distinct first
     words in 30 replies**; canon spreads across I / you / what / it's / so / no.
     **bugs.md 77 did not hold.** It took `"W-what"` 83% → 37%; it is back at 33.3% plus 13.3%
     of `"Wh-what"`, which is the same tic wearing a different spelling — **and a scorer that
     matches one spelling will report success while the crutch survives.** Match the FAMILY.
     **Do not fix this with another list** (CLAUDE.md 45): compulsory + enumerated is the
     strongest phrase-supplier there is, and it is what produced both crutches. Replace the list
     with a RULE FOR FORMING the deflection, and check the replacement against CLAUDE.md 43
     before shipping — the last two replacement lines both began "Don't", which is how 13%
     became 33% in the first place.
     **Method that worked before:** `dev/prompt_lint.py` first, then `dev/canon_gap_probe.py
     --arm X` as an in-memory transform (it never writes to `amadeus.html`), then
     `dev/canon_likeness.py --validate` for the noise floor and `--compare`. Watch the quality
     guard: deflection rate and tsundere tag rate must hold, and the everyday-chat control
     (#181) must stay clean. **Then Zani judges by ear — no metric can close this.**
     **Original entry below.**

180. **`"Don't"` is now the second opener crutch: 13% → 33%, and bugs.md 77 caused it.**
     Two replacement exemplars written for bugs.md 77 both open on "Don't", which is precisely the
     mistake the old prompt made with "W-what". Canon opens with "don't" **1.9%** of the time.
     The arm that fixed the duplication measured no better (27% vs 33%, p=0.78) — so the exemplars
     are probably not the whole cause and the next attempt should not assume they are.
     Also still open from bugs.md 77: the "what"-family opens **50%** of flirty replies (canon: 1 line
     in 1,672) and distinct openers are **7/30** (canon: 34 in 64). Harness and both arms are on disk
     (`dev/canon_arms/HMPH_*`), so a new arm is ~60s and ~1,100 output tokens.

181. ✅ **DONE (Sep 3, 2026) — RAN CLEAN, no regression.** See bugs.md 77b item 3 for the table.
     The BEFORE arm was read from `git show 8b0b953~1:amadeus.html` via the new `--prompt-rev`
     flag, so it is the real shipped prompt rather than a hand-reverted approximation — reuse
     that flag for any future before/after arm. *(Original entry:)* **bugs.md 77 has no daily-life regression control — "no regression" is an assumption.**
     Found Sep 3, 2026 in the 77b self-review. bugs.md 77 changed the CASUAL rule line and the
     INPUT→EMOTION line, then measured **only** on tsundere probes. Everyday conversation, where
     most turns actually happen, was never re-measured. The #176 daily-life baseline was lost with
     the cleared scratchpad, so this needs two fresh arms — `--probes daily` at HEAD and at
     `git show 8b0b953~1:amadeus.html`. ~2 min, ~1,700 output tokens, app closed (CLAUDE.md 37).
     **Check length distribution AND the #176 figures** (0% of replies ≤8 words, 3.13 sentences
     per turn) so a shape regression cannot hide behind an unchanged tic rate.
     **Do this before trusting bugs.md 77 beyond flirty messages.**

182. **The diary WRITE-GATE was approved, investigated, and dropped — the generator is fine.**
     Sep 3, 2026. Zani approved a write-gate to stop lab-prose diary entries. Measuring first
     killed it: deduplicated and split at the date bugs.md 69 shipped, clinical entries went
     **27% before → 0/6 after**. An earlier "5/10 recent entries clinical" reading was wrong —
     an artefact of triplicated rows (bugs.md 78) plus a false positive on *baseline* used
     normally. **bugs.md 69 works. Do not rebuild this gate without new evidence.**
     What the investigation found instead was bugs.md 78, a 30% duplication defect.
     **Lesson: a keyword classifier is a screen, not a verdict — read the actual rows before
     concluding a shipped fix has failed.**

183. **#161 quantified: 13 legacy clinical diary entries, and they are the last piece.**
     Measured Sep 3 on the live collection, deduplicated: **13 of 49 pre-fix unique entries**
     contain lab vocabulary; 0 of the 6 written after bugs.md 69. They are still retrieved —
     Zani's Sep 3 turn capture caught *"pattern recognition issue"* and *"internal systems"*
     injected on an ordinary conversation. bugs.md 78 removed the amplifier (duplicates gave
     some of them up to 5x retrieval weight); the entries themselves remain.
     **TOOL BUILT Sep 3 (awaiting Zani's review, nothing applied):** `window.rewriteClinicalDiary()`
     in `amadeus.html`, dev-only, matching the `dumpLastTurn()` pattern. Dry run by default: it
     prints BEFORE/AFTER for every flagged entry and writes nothing. `{apply:true}` backs the whole
     diary array up to its own `localStorage` key first, then writes. It **rewrites, never deletes**
     (bugs.md 71). Three guards keep the ORIGINAL rather than store a bad rewrite: a truncated
     generation (CLAUDE.md 40), a rewrite that is still flagged, and one that lost >50% of its
     length. It also handles #184 in the same pass. Afterwards it downloads the list of replaced
     texts for `dev/dedupe_diary.py --prune`, because the originals stay in ChromaDB otherwise and
     BOTH versions would be retrievable.
     **FIRST DRY RUN, Sep 3 (n=16 flagged entries): 9 rewritten cleanly, 7 kept as-is.** All seven
     failures were the same thing — one lab word survived the rewrite. None truncated, none too
     short, so the guards behaved. The 9 accepted rewrites were read and are faithful: *"threw my
     processing unit into an inefficient state"* → *"threw me off balance"*, *"a bizarre spike in
     operational anomaly"* → *"a bizarre jolt"*. Several also dropped the banned *"Honestly,"*
     opener as a side effect — an improvement, but more than the stated scope, so it is recorded.
     **Two defects in the tool, found by that run and fixed the same day:**
     (a) **apply re-generated instead of saving what was reviewed.** Generation is stochastic at
     temp 0.4, so Zani would have approved one text and stored a different one — a review he cannot
     trust is worse than no review. The dry run now caches its results and `{apply:true}` commits
     exactly those (`{apply:true, regenerate:true}` to force fresh ones). Both paths share one
     `_diaryCleanupCommit()` so they cannot diverge.
     (b) **no retry.** A rejected entry rewrote cleanly when run alone, so the failure is sampling
     noise, not an impossible entry. Now up to 3 attempts, naming the words that actually survived
     and raising temperature each time (a retry at the same temperature reproduces the same
     failure). Naming them is safe under CLAUDE.md 43 here because this is a one-shot constrained
     EDIT whose output is verified by the guard, not free generation across turns.
     **Deliberately NOT a retrieval-time filter:** that needs permanent code plus a keyword list
     already observed to produce a false positive (*baseline* used normally), and in a filter a
     false positive silently hides a real memory forever.
     **Options, unchanged and still Zani's decision:** rewrite them in plain words offline
     (bugs.md 69 showed rewriting works and preserves content — dropping them does not, and
     bugs.md 71 rejected a variant that halved what she remembered), re-index, or let attrition
     handle it. **Rewriting is a one-off offline job with the app closed; it touches his real
     diary history, so it needs an explicit yes and a backup.**

184. **"Don't get the wrong idea" is regenerating itself through her diary.**
     Found Sep 3 in Zani's turn capture. bugs.md 76 removed the phrase from `SYSTEM_PROMPT`
     and drove it 37% → 3%. But she had already written it into a diary entry dated
     31 Aug — *"the way he insisted I *don't* get the wrong idea kept echoing in my head"* —
     and **the diary is injected into every prompt**. She said the phrase again on the first
     turn of the Sep 3 session. **A prompt fix does not hold if the phrase survives in memory.**
     This is CLAUDE.md 42's feedback loop applied to a catchphrase rather than a register.
     Only **1** entry of 55 is affected, so this is small today — but it is the mechanism that
     will undo any future phrase-level fix. **Cheapest correct fix is probably a check on the
     diary WRITE path for phrases absent from canon** (`dev/prompt_lint.py` already does exactly
     that comparison and could be reused), NOT a broad register gate — see #182 for why that was
     dropped. Measure before building: n=1 is not yet evidence of a rate.

185. **Nit: `main.js:610` says "a full 9.5GB RELOAD".** That figure is the model's DISK size, and
     the comment is about disk I/O, so it is defensible — but it reads like a memory figure, which
     is what backlog #172 spent a session untangling. Reword to say "disk read" explicitly.
     Left alone on Sep 3 only to keep that session's deployment story clean (`main.js` needs a
     rebuild; everything else that day was relaunch-only). Comment-only, zero functional impact.

## N. Presence — the Jarvis direction (186–190), opened September 4, 2026

Zani's north star: real-time support like Jarvis, with Kurisu's personality, voice and
appearance kept exactly as they are. He chose **presence before awareness** on Sep 4.
Presence is a LATENCY problem, not a feature list. The five parts were scoped as P1–P5;
only P1 is built.

186. ✅ **DONE (Sep 4, 2026) — P1: the presence latency trace.** Ships the instrument, not a
     fix. Records ONE headline number per turn — **he stops talking → she starts talking** —
     plus the per-stage breakdown (Whisper, RAG, prefill, first token, generation, translate,
     Fish, first audible sample). `amadeus.html` + `kurisu_fish_server.py`, **no rebuild.**
     - **Why it comes first:** P3 (streaming TTS) is a real renderer refactor with a permanent
       cost to her prosody. It must not be bought on a guess. If translate+Fish is most of the
       wait, P3 pays; if prefill or generation dominates, the lever is `num_predict` or the
       ~431-token RAG block (#160) instead.
     - **It also creates the BEFORE arm.** This project has been bitten twice by a missing
       baseline (#176's raw output was lost; bugs.md 77b shipped with no everyday-chat control).
     - **DevTools:** `latencyStatus()` (medians, per stage, optionally filtered by kind),
       `latencyDump()` (→ `~/Downloads/amadeus_perf.json`), `latencyReset()` (clear between arms).
       One console line prints per turn, so the numbers are visible while he uses her.
     - **Kill switch:** `PERF_TRACE=false` in `amadeus.html` + relaunch. No code revert needed.
     - **Cost:** no model, no GPU work, no extra Ollama call. A full 200-turn ring measures
       **~50KB of localStorage** (258 bytes/row, measured). Storage is written AFTER her audio
       starts, so it is outside the path being measured.
     - **Tests:** `node dev/perf_trace_test.js` — 45 checks. It extracts the shipped block out
       of `amadeus.html` by anchor rather than testing a copy.
     - **Two traps it exposed → CLAUDE.md 48:** instrumentation must never throw into its
       caller (`sendMsg`'s catch runs `history.pop()`), and every clock opened must be closed
       or aborted on all four exit paths that never reach a reply.
     - ✅ **LIVE-VERIFIED on the TEXT path (Sep 6, 2026, n=4).** Records, closes every turn, and
       cross-checks: renderer TTS round trip 2859ms vs the Fish server's own 1430+1420=2850ms —
       two processes, two clocks, 9ms apart. **The voice path is still untested live** (all four
       turns were `kind:'text'`, so `stt` has never run in the app). Its first run found a defect
       in itself → bugs.md **79**.
     - **Needs an evening of normal use before the medians mean anything** — n>=30, per this
       file's own standing rule. Five turns are noise.

187. **P2 — barge-in: let him interrupt her.** Today the mic is OFF from the moment he stops
     speaking until 600ms after her reply ends (`hfPauseListening()` in `hfSubmit`, re-armed by
     `hfMaybeRelisten`, `HF_RELISTEN_DELAY_MS=600`). Barge-in reverses that deliberate choice —
     #53 deferred it, so it needs a fresh decision, and it now has one.
     **Three parts, and the third is the one that bites:**
     (a) keep the VAD running while she thinks and speaks; (b) on confirmed speech stop her
     audio and fade the mouth closed (bugs.md 26 / CLAUDE.md 39 govern the teardown);
     (c) **history integrity — an interrupted reply is a fragment, and CLAUDE.md 40 / bugs.md 67
     forbid storing one.** Store only what she actually SPOKE, trimmed to a complete sentence.
     `echoCancellation:true` is already set on all three `getUserMedia` sites, which is the
     right starting point, but her voice still reaches the mic — expect to need a raised
     threshold and a minimum-duration guard while she is speaking.
     Industry target for reference: barge-in under 150ms; human turn-taking is ~200ms.
     **Cost: no new model, no GPU. It uses the vendored Silero VAD that already runs.**

188. ❌ **BLOCKED by CLAUDE.md 51 (2026-09-07). Do not start without a fresh decision from Zani.**
     Per-sentence synthesis breaks the audio-duration subtitle sync (bugs.md 6), and the display
     layer is frozen at his instruction. The analysis below stays for the day that changes.
     Note the measured ceiling is smaller than it first looked: translate must run on the
     COMPLETE English text in any CLAUDE.md 37-compliant design, so streaming can only attack
     the Fish half — about 0.7-0.9s of a ~4.8s wait.
188b. **P3 — faster first audio. Two designs; measure P1 first.**
     Today the path is fully serial: `sendMsg` awaits the WHOLE Ollama stream, then makes ONE
     `/speak` call, which does one translation then one Fish call returning one MP3.
     - **Option B of #153 (per-sentence HTTP).** Known quantity. Pays Fish's fixed per-call
       overhead each sentence and leaves a 30–100ms MP3 seam.
     - **Fish Audio WebSocket streaming — NEW, and #153 did not know about it.**
       `wss://api.fish.audio/v1/tts/live`, MessagePack, text streamed as events, server-side
       buffering via `chunk_length`, a `flush` command for immediate synthesis, and a `latency`
       mode of normal/balanced/low. This removes BOTH costs #153 called unfixable.
     - **Both keep ONE gemma4 translation on the finished English reply.** That is what keeps
       CLAUDE.md 37 satisfied. #153's Option A (translate per sentence, during generation)
       stays rejected — it fires gemma4 calls on the GPU that renders her.
     - **The blocker is subtitle sync, not the audio.** `msPerWord` is computed from
       `audio.duration` at `loadedmetadata` (bugs.md 6). A stream has no duration until it
       ends, so streaming needs MediaSource plus a different reveal clock.
     - **#153's Phase 0 is already answered.** It asked for a sentence count before anyone
       builds this. bugs.md 77b measured **3.23 sentences per turn**, so her real replies sit
       at the TOP of #153's estimated 1.5–3s saving, not the bottom.
     - **First live datapoint (Sep 4, n=1, app closed, gemma4 warm, 21-word input):**
       translate **1195ms** + Fish **1208ms** = ~2.4s in the TTS stage alone. **n=1 — this is
       an instrument check, not a result.** Wait for P1's medians.

189. ✅ **DONE (Sep 7, 2026) — see bugs.md 81. NOT live-verified.** Shipped as the thinking
     indicator: the three dots that already existed but had never been visible, because
     `sendMsg` switched them on and off in the same synchronous block. They now run from Enter
     until her words appear, and the subtitle carries only her words.
     **Deliberately NOT built: the Live2D "attention beat".** I predicted it would be near
     invisible — when Zani types, his mouse is idle, so `restBlend` has already drifted her gaze
     forward — and it would have touched the `focus()` head pipeline that sits beside the
     lip-sync machinery behind bugs 22/23/25. Building something expected to be invisible, in
     the most delicate part of the renderer, is a bad trade. **Revisit only with a reason.**
     Original scoping below.
189b. **P4 — instant visual acknowledgement, no inference.** The moment his speech ends, she
     reacts visually: expression change, head turn, a listening→thinking state. No audio, no
     model call, no `history` write. It hides the remaining wait at zero cost.
     **Keep it visual.** The spoken equivalent (a backchannel, "Hm.") would be a supplied
     phrase (CLAUDE.md 43) and must never enter `history` (CLAUDE.md 47).

190. **P5 — semantic turn detection. Later, and it is the only part that costs RAM.**
     Today the turn ends after a fixed 900ms of silence (`HF_REDEMPTION_MS`), so a pause to
     think reads as a finished sentence. `HF_RESCUE_RE` (trailing "and"/"but"/"um") is already
     a cheap local approximation of this.
     SOTA is an end-of-utterance model: LiveKit's is a 135M-parameter transformer over the last
     four turns; Pipecat's reads prosody from audio with no transcript. **Cost this properly
     against the 4.10 GiB anchor before proposing it** — it is the only presence item that
     moves resident memory.

191. ⚠️ **Fish Audio API credit is EXHAUSTED — her voice is DOWN in the app right now.**
     Found 2026-09-06 during the #186 offline probe: turn 15 of 30 onward returned
     `402 Insufficient API credit`. **This is not a probe problem — it is her live voice.**
     `ttsSpeak` gets a 500 from `/speak`, catches it, and falls back to
     `startEstimatedReveal()`, so she still shows her words and the app never breaks. She is
     simply SILENT, with no error shown on screen (only in the console).
     **Fix is Zani's, not code:** top up at `https://fish.audio/app/developers`. **API credit is
     billed separately from platform credit** — the error says so explicitly, so a funded
     Fish account can still have zero API credit.
     **Worth a design follow-up either way:** a credit failure and a network failure are
     indistinguishable on screen. A 402 is permanent until he pays; a timeout is transient.
     The UI should probably say "voice unavailable" for the former rather than silently
     falling through — otherwise the next silent session gets diagnosed as a bug in the TTS
     code. Related: bugs.md 2 (never require `char_timings`), #34 (the /speak timeout).

192. **`dev/latency_probe.py` — measure the pipeline without talking to her (built Sep 6, 2026).**
     Zani asked for P1's numbers without holding 30 real conversations, and specifically asked
     that nothing reach her diary. Driving her chat automatically would have written 30 false
     memories: every turn enters `history`, is rolled into the diary on close, feeds
     `maybeExtractFacts()` (→ `amadeus_facts_v1`, injected into EVERY future prompt), and bumps
     the relationship score. **That constraint was correct and it shaped the tool.**
     - Runs `live RAG → gemma4 → /speak` outside the app. Covers every stage of the wait
       **except STT and ~3ms of playback start**.
     - **The prompt is a REAL captured turn** (`~/Downloads/amadeus_turn.json`, richest row =
       4248 prompt tokens), minus its trailing RAG block and user message. Rebuilding the prompt
       instead would have missed the diary/facts/relationship blocks that live in localStorage
       and come out ~1,000 tokens short — prefill would then read optimistically low.
     - **Proves it wrote nothing:** Chroma row counts for all four collections plus a sha256 of
       `chroma.sqlite3`, taken before and after, printed side by side.
     - Refuses to run while the app is open (CLAUDE.md 37).
     - **Two defects the first run exposed in the tool itself, both fixed:** (a) the 'before'
       hash was taken AFTER importing `kurisu_rag_server`, which re-upserts the behavior rules —
       so `before == after` looked like a clean proof while the file had in fact churned; the
       baseline hash is now taken before any import, and the churn is reported and explained.
       (b) turns whose TTS failed have a `total_ms` that EXCLUDES the TTS stage, and mixing them
       into one median understated the wait; complete and partial turns are now reported apart.
     - **Known bias, and it is large — see #193.**

193. **The offline probe runs on an IDLE machine; the app does not. Prefill differs ~1.6x.**
     Measured the same day, same prompt size (~4,200 tokens): the probe reads **598ms** median
     prefill, the live app read **855–1004ms** (P1, n=4). The probe has no Live2D rendering, no
     WebGL, no BGM and no Electron competing for the GPU that gemma4 runs on (CLAUDE.md 37).
     **So the probe UNDERSTATES the real wait, and it understates the gemma4 stages
     specifically** — prefill, generation and translation are all GPU-bound, while Fish is a
     network call and is unaffected. That means the probe also **understates the gemma4 SHARE**
     of the total.
     **Use the probe for A-vs-B comparisons and for stage proportions. Use P1's live numbers for
     any absolute claim.** Do not quote a probe total as "the wait".

194. **UNDOCUMENTED ASSET: a full local Fish Speech S2 Pro sits in `~/Documents/Kurisu_Dataset_Pro`
     (14 GB), and no doc mentioned it until now.**
     Found 2026-09-06 because Zani said "I think I downloaded the s2 model" — he was right and I
     had been reasoning as though the cloud API were the only option. **The HuggingFace cache
     entries (`models--fishaudio--s2-pro` etc.) are empty 4KB shells with only a `refs/main`
     pointer — do not be fooled by those.** The real files are:
     | path (under `~/Documents/Kurisu_Dataset_Pro/`) | size |
     |---|---|
     | `fish-speech-s2/checkpoints/s2-pro/` (2 safetensors + codec.pth) | **10 GB** |
     | `fish-speech-s2/checkpoints/fish-speech-1.5/` | 1.4 GB |
     | `fish-speech-s2/venv_s2/` (torch etc.) | 1.7 GB |
     | `kurisu_*.wav` — the voice dataset | **756 clips** |
     `awaken_amadeus.py` is a working experiment, but it drives **fish-speech-1.5**, not s2-pro,
     zero-shot from `kurisu_0052.wav` on `--device mps`.
     **`results/` does not exist — the fine-tune was never run.** That matches roadmap.md's
     "local fine-tuning of S2 weights impossible on 16GB Mac (~20GB RAM)".
     **Three reasons this is NOT a drop-in replacement for the cloud TTS, all of which need
     stating before anyone gets excited:**
     1. **RAM is UNMEASURED. 10 GB is the DISK size.** Do not repeat #172's mistake in reverse:
        gemma4 is 9.6 GB on disk and 4.10 GiB resident because it is quantised and mmap'd, but
        safetensors typically load far closer to 1:1. Estimated ~8–10 GiB resident against a
        16 GB machine that already holds gemma4 at 4.10 GiB plus Electron and four python
        servers. **Measure the real RSS before designing anything around it.**
     2. **The voice does not carry over.** `reference_id c4d832799bf845ee86638a1bc0cd0d41` is a
        Fish-HOSTED voice. Local inference clones from a reference WAV instead, so she would
        sound like `kurisu_00XX.wav`, not like the voice Zani has actually been listening to and
        tuned in the July A/B.
     3. **It would run on the GPU that renders her.** CLAUDE.md 37 exists precisely because
        gemma4 already contends with her Live2D. Local TTS inference there works against the
        whole presence effort (#186–#190), not for it.
     **Cheap next step if it is ever wanted:** load `checkpoints/s2-pro` with the app CLOSED and
     read the actual RSS. That converts the estimate above into a number and settles whether
     local TTS is possible on this machine at all. ~10 minutes, installs nothing.

195. ✅ **DONE 2026-09-07 — see bugs.md 83.** Fixed with an idle timer re-armed on speech plus a
     separate 60-min absolute cap, so #56's battery intent survives. `node dev/hf_boot_test.js`.
     **Original report below.**

195b. **`HF_SESSION_MAX_MS` is a hard session cap, not the idle timeout its comment claims.**
     `hf.sessionTimer` is armed once in `hfStart` (`amadeus.html:3519`) and cleared only in
     `hfStop` (`:3529`). **Nothing resets it on speech.** So a hands-free session always ends
     10 minutes after it STARTS, even mid-conversation — the comment says "auto-end a silent
     session (#56, battery)" but silence is never checked. Found 2026-09-06 while telling Zani
     how to run the P1 voice check.
     **Low harm** — he taps to talk again and `hfStop` even rescues held text. But it fires
     during active use, which is not what #56 asked for, and a long voice session is exactly the
     case the presence work (#186–#190) is trying to make pleasant.
     **Fix if wanted:** re-arm the timer in `hfOnSpeechStart` (and/or `hfSubmit`) so it measures
     idleness rather than wall time. **Check the battery intent of #56 first** — an always-resetting
     timer means a forgotten session never ends, which is what the cap exists to prevent. A
     two-timer design (idle timeout + a longer absolute cap) is probably what was meant.

196. ✅ **CLOSED 2026-09-07 — THE TRANSLATE STEP IS 1019ms AND NOTHING CHEAP CUTS IT.**
     All four candidate arms were measured against the shipped code and all four failed.
     **Do not re-run them.** The instrument is `dev/translate_probe.py` (decomposes the call
     via Ollama's own counters, spends NO Fish credit) and `dev/translate_register.py`
     (scores Japanese register). Arms are in `dev/translate_arms/`.
     **NOISE FLOOR FIRST:** n=30, run-to-run delta **6ms**, bootstrapped 95% CI half-width
     **~100ms**. A difference under ~100ms at n=30 is not a difference.
     **The baseline decomposition (n=60 pooled, app closed, Ollama 0.33.3):**
     | stage | median | share |
     |---|---|---|
     | whole call | **1022ms** | 100% |
     | model load | **0ms** | 0% — `keep_alive:'30m'` works |
     | prefill (175 tok) | 240ms | 23.8% |
     | **decode (29.5 tok)** | **786ms** | **77%** |
     **It is decode-bound at ~27ms per output token.** Nothing about the prompt touches decode.
     **The four arms:**
     - ❌ **DeepL — fast, and it fails register.** 392ms vs 1022ms (saves ~780ms live), 0/30
       failures. But on the same 30 real replies: feminine endings **56.7% → 23.3%**, polite
       です/ます **0% → 6.7%**, calls him 君 **0% → 20%**, あんた/あなた **16.7% → 3.3%**, and one
       masculine ending. It writes paper prose for her science lines (時空の曲率から直接生じる
       現象**である**) — the same failure the July A/B recorded, reproduced on 30 lines instead
       of 8. **It also invented a fact:** "keeping track of your hours" became 君の**勤務時間**
       (your work shift). That is a correctness failure in something she says aloud, not taste.
       **Zani's constraint stands. Rejected.**
     - ❌ **`num_predict` — not a lever at all.** 0/30 truncated; decode stops at EOS around 30
       tokens against a cap of 150 (3.3x headroom). Lowering the cap saves **zero** ms and only
       adds truncation risk. The idea in the pre-close version of this entry was wrong.
     - ❌ **A smaller local model — not faster.** `gemma3:4b` measured **1015ms** vs gemma4's
       1022ms: a 7ms difference against a ±100ms floor. It decodes 13% faster per token and
       writes more tokens, cancelling out. `qwen3:4b` is a reasoning model — with `think:false`
       the reasoning leaks into `content`, without it the whole budget goes to thinking and
       `content` is empty; 150/150 tokens and 100% truncated at 3630ms. Both models were
       deleted after measuring; `ollama list` is back to `bge-m3` + `gemma4`.
     - ❌ **Overlap (translate while she is still writing) — cannot pay.** `llama-server` runs
       with **`-np 1`** (read off its command line), so a second request QUEUES rather than
       overlapping: generate alone 2358ms, translate alone 661ms, run concurrently the translate
       took 2795ms and finished no earlier. Generation was NOT slowed, but only because nothing
       actually overlapped. Overlap needs `-np 2`, which the next bullet shows buys nothing else,
       plus renderer changes and partial-sentence translation that risks register.
     - ❌ **`OLLAMA_NUM_PARALLEL=2` — nothing to fix.** See the KV correction below. **Not
       changed; `launchctl` was never touched.**
     **THE +0.57s KV PENALTY NO LONGER EXISTS — corrected 2026-09-07.** The July figure was
     WALL time of a 3-token request, which mixes prefill, decode and scheduling. Re-measured as
     `prompt_eval_duration`, the penalty is **+2ms** (one intermittent re-prefill in 4 calls; over
     10 alternating chat→translate turns the chat prefill held at **148ms for 5,322 tokens**).
     So translate costs 1270ms live and nothing extra on the following turn. Any future
     reasoning that leans on the +0.57s figure is leaning on a stale number.
     **WHAT STILL CUTS TRANSLATE:** only fewer output tokens, because decode is 77% and scales
     with them. That is **#176** (her replies are 13–22 words; canon is ≤8 words half the time)
     — a change wanted for character reasons that would cut translate as a side effect. On these
     numbers, halving her reply length is worth roughly 390ms per turn.
     **AND THE REAL PRIZE IS NOT HERE — see #160**, which this investigation measured by
     accident and which is larger than anything translate had to offer.


197. **Flirty messages retrieve the WRONG behaviour rule — and some of them are injected.**
     Found 2026-09-12 (#180). Top-1 behaviour rule for the 30 tsundere probes: `amadeus_existence`
     11, `kurisu_research` 10, `user_shares_news` 4 — never `affection_love`. Six were below 0.5 and
     injected, e.g. "i like talking to you" → `amadeus_existence`, which says *"No deflection on this
     topic"*, the opposite of the ROMANTIC rule. Of 40 screened confession/appearance messages,
     "you're attractive" and "i love the way you talk" inject `kurisu_research`. Top-1 + a single
     global threshold cannot separate these. Not measured for effect on replies yet.
198. **`affection_love` and `compliment_appearance` contain the CLAUDE.md 45 construction and are
     inert today.** `kurisu_rag_server.py:79`: *"Open with a stammer — W-what, I-I, Th-that's"*;
     the second ends its example with *"Don't."* bugs.md 77 removed this pattern from SYSTEM_PROMPT;
     a copy survived here. **Injected 0 times in 478 logged retrievals** (2026-07-21 → 09-12), so it
     is not causing #180 — but any threshold or embedding change (#197) would switch it on. Rewrite
     it as a forming rule when #180's wording is settled. It is stored in Chroma: after an edit,
     restart the RAG server and VERIFY the stored document changed (bugs.md 78's trap).
199. **`canon_likeness.py` quality guard has two blind spots.** `STAMMER_RE` (`\b([A-Za-z])-\1`)
     does not match `Wh-what`. `DEFLECT_MARKERS` includes "don't get" and "don't be", so a fix that
     removes "Don't" lowers the deflection rate by construction — the circularity
     `check_guard_independence()` exists to catch, from the reply side instead of the prompt side.
     `dev/opener_family.py` has a family-aware stammer count; the deflection guard still needs
     either marker-free classification or a blinded read by eye.
200. **`latencyDump()` names a path it may not have written.** Found 2026-09-22. It always downloads
     as `amadeus_perf.json` and always logs `→ ~/Downloads/amadeus_perf.json`. `main.js` has no
     `will-download` handler, so when that file already exists the new dump is likely saved under
     another name (e.g. `amadeus_perf (1).json`) while the console names the OLD file. The 2026-09-06
     dump sits there today, so the next dump will hit this. Risk: someone analyses stale data and
     believes it is new. Workaround: take the newest `amadeus_perf*.json` and check `capturedAt`.
     Possible fix: a timestamped filename. It is instrumentation, below the display layer.
201. **Silero VAD has never loaded — every hands-free session runs on the RMS fallback.** Found
     2026-09-27 from Zani's console: `Encountered an error while loading model file
     vendor/vad/silero_vad_v5.onnx`, then `[HandsFree] Silero unavailable, falling back to RMS engine:
     no available backend found. ERR: [wasm] TypeError: Failed to resolve module specifier
     'vendor/vad/ort-wasm-simd-threaded.mjs'`. Hands-free still works (`session started (adaptive-RMS
     fallback)`), and turns log as `voice-rms`.
     **Cause — two faults, both present since vendoring on 2026-07-18 (`3446f98`, loader `b5714d4`):**
     (1) `bundle.min.js` (vad-web 0.0.30) embeds **onnxruntime-web 1.22.0**, whose wasm backend
     dynamic-imports `ort-wasm-simd-threaded.mjs` (+ its `.wasm`). `vendor/vad/` holds only the
     **1.17.3** files (`ort.min.js`, `ort-wasm.wasm`, `ort-wasm-simd.wasm`) — the file it asks for does
     not exist. (2) The prefix `'vendor/vad/'` makes `import('vendor/vad/…mjs')` a BARE module
     specifier, which a browser refuses before it even looks for the file; it needs `./vendor/vad/`
     or an absolute URL. No doc records Silero ever verified live.
     **Effect:** RMS is the designed fallback, worse at rejecting background noise; Silero was meant to
     be primary (#49). The window-level `ort.min.js` 1.17.3 (542 KB) is loaded and apparently unused.
     **Fix sketch (needs Zani's yes — it DOWNLOADS files):** vendor onnxruntime-web **1.22.0**'s
     `ort-wasm-simd-threaded.mjs` + `ort-wasm-simd-threaded.wasm`, set `wasmPaths`/`onnxWASMBasePath` to
     `./vendor/vad/`, then confirm the console no longer warns. Measure RAM/CPU of the worklet first
     (standing order). Low priority while Zani is a text-first user.

## O. From the 2026-09-27 silent-fallback audit (202–215)
Read-only audit, every fallback found by grep. Full table: session-log.md, 2026-09-27 (audit) entry.
**Evidence window:** P1 ring (52 turns, 2026-09-06 → 09-27), `data/rag_trace.log` (1496 lines since
2026-07-21), Ollama `server.log` (chat detail only for 2026-09-27), localStorage and ChromaDB read from
copies. **No app code, data or ChromaDB was changed.**

202. ✅ **FIXED 2026-09-27 — bugs.md 92 (close pass + salvage + run log). Live-verified the same day: close run ok, 3 facts stored; the idle pass also ran and stored.** **The facts store has NEVER been written — 0 facts in 21 sessions since the bugs.md 64 fix.**
     Evidence: `amadeus_facts_v1` is absent from localStorage (log AND table decoded, 2026-09-27); no
     code path deletes it (`grep removeItem\|localStorage.clear` → only `latencyReset`). The trigger fix
     shipped 2026-08-11 (`a966a00`); 21 diary sessions since then, 5 of which name a durable topic
     (a mock exam, a trip, piano, a football match). **The model is NOT the cause:** a replay of the
     shipped prompt (pulled from `amadeus.html` by anchor, app closed) returned 3 facts in 3/3 runs on a
     fact-dense chat, and `{"facts":[]}` (5 tokens) in 3/3 on a light chat. The one live run in the
     Ollama log (2026-09-27 12:53:03, temp 0.2, 5 tokens) was on a light chat and fits `{"facts":[]}`.
     **UPDATE 2026-09-27 (later) — the gate hypothesis is WEAKENED.** Real timing (P1 send times +
     `rag_trace.log`) shows long quiet gaps in most sessions right after fact-bearing messages
     (2026-08-23: 112s, 98s, 300s, 469s), hands-free was OFF (`amadeus_voice_first=0`), and only real
     input moves the idle clock. So the extractor probably DID run and returned nothing. A replay of the
     shipped prompt on his REAL messages (13 sessions since the fix, first 80 chars from the trace,
     his side only) found facts in **2 of 13 sessions** (7 facts, 0 parse failures) — the model is
     conservative, and at a lull it sees only the last 12 lines, so a fact said earlier can fall out
     of the window before any lull. **Cause is UNKNOWN between "did not run" and "ran, saw nothing".**
     The plan must work for both and must record every run (CLAUDE.md 52).
     **OUTPUT-LIMIT PROBE for the approved close-mode plan (2026-09-27, app closed, shipped prompt by
     anchor, temp 0.2, seeds 1000+):**
     | Input | Known facts | `num_predict` | n | Cut / unparseable | eval median / max | time median / max |
     |---|---|---|---|---|---|---|
     | dense 4800 chars (20 facts) | 40 | 500 | 30 | **30/30** | 500 / 500 | 14.0s / 16.3s |
     | dense 4800 | 40 | 2000 | 10 | 0/10 | 583 / 611 | 16.1s / 16.8s |
     | dense 4800 | 40 | 800 | 30 | **1/30** (seed 1018) | 586 / 800 | 16.1s / 21.8s |
     | dense 4800, seed 1018 only | 40 | 3000 | 1 | 0/1 — same 18 facts, verbose form | 978 | 26.8s |
     | dense 2400 (chunk) | 40 | 500 | 30 | **12/30** | 495 / 500 | 13.4s / 15.2s |
     | realistic 4800 (3 facts) | none | 800 | 30 | **0/30**, 3/3 facts every run | 132 / 172 | 3.6s / 5.4s |
     ~32–54 tokens per fact. **The shipped in-session path (2400 chars, 500) also cuts 12/30 on a dense
     chat** — bugs.md 73's fixture was less dense. Chunking does not fix it. Realistic headroom at 800 is
     4.65x; the dense extreme still cuts 1/30 at 800, and a safe cap there would cost ~27s at close.
     *Original hypothesis, kept for history:* the gate. `_factsIdleOk()` needs 45s with no activity OR a
     hidden window, and never during hands-free; his sessions are short, with replies ~20–40s apart,
     and end with a close — the same "trigger unreachable" shape bugs.md 64 described. The 12:53 run
     happened only because the window was hidden. **Also seen:** 1 of 3 replay runs dated the exam
     2024-10-14, not 2026 (event_date year). **Next step (needs Zani's yes — it is code):** make the
     extractor record each run and result somewhere that persists (see #204), then decide the trigger
     — e.g. run it at close, before the diary, where the diary call already runs.
203. ✅ **FIXED 2026-09-27 — bugs.md 93 (not live-verified).** **The four Python servers' stdout/stderr are PIPES that nothing reads — output is lost, and a
     full pipe BLOCKS the server.** `main.js` spawns tts/http/rag/whisper (`spawnTtsServer` etc.) with
     no `stdio` option (= `'pipe'`) and never reads `proc.stdout`/`proc.stderr`
     (`grep '\.stdout\|\.stderr' main.js` → nothing). Node's docs say a child that fills an unread pipe
     blocks. **Measured 2026-09-27** with a toy child under Node (not the app): it stopped after 1311
     × 100-byte lines ≈ **131 KB** and never finished. The fish server prints ~**860 B per `/speak`**
     (7 lines, incl. the full tagged Japanese), so print() would block after **~150 spoken replies in
     one app launch** (+8 KB Python buffer). The server would then hang mid-request: `ttsSpeak` times
     out at 20s, she goes silent with a text reveal (`note:'tts-timeout'`), the watchdog sees no exit.
     **Not yet reached:** the longest launch in the evidence had ~30 `/speak` calls (19 replies +
     greeting + warmer). RAG (~300 B/turn) and Whisper (~150 B/utterance) have more margin.
     Verdict **BROKEN (latent)**. Fix sketch: pipe each child to a rotating file in `data/logs/` —
     this also gives #204 its evidence. Needs a rebuild (`main.js`).
204. ✅ **FIXED 2026-09-27 — bugs.md 93: data/logs/ (not live-verified).** **No persistent log sink: main.js, the renderer console and all server output vanish at close.**
     Nothing hooks `console-message`, no file stream exists, `~/Library/Logs` has no Amadeus folder.
     This is the root reason 7 of the fallbacks below (#208–#214) are **UNKNOWN**: their only trace is a
     `console.warn`. The only lasting evidence today is `rag_trace.log`, the P1 ring, Ollama's own log
     and localStorage. Also: `/retrieve`'s error branch (`kurisu_rag_server.py:438`) returns HTTP 200
     with empty lists and writes NO trace line, so a server error looks the same as "nothing matched"
     to the renderer AND leaves no record (it did not happen in the window: 52/52 P1 turns have a trace
     line). Fix sketch (needs his yes): one rotating `data/logs/` file per process, and a trace line
     for the RAG error branch. Design it with #203; state its disk cost first.
205. **The Whisper no-speech gate let a repetition hallucination through.** `rag_trace.log`
     2026-09-27 12:52:02 holds the query "What a great deal, a great deal, a great deal, …" (cut at 80
     chars) — the first voice turn of that session (P1 `voice-rms`, `rescueHoldMs 1600`). A phrase
     repeated 6+ times is Whisper's typical output on non-speech. The gate (`amadeus.html`,
     `hfHandleUtteranceBlob`) checks only `no_speech_prob` and `avg_logprob`, so she replied to it.
     n=1; RMS (#201) passes more noise to Whisper than Silero would. ✅ **CONFIRMED 2026-09-27: Zani did NOT
     say it** — a hallucination reached her. BROKEN. Possible fix: a repetition check on the transcript. Not a display change.
206. **Cold boot: the RAG readiness gate and the renderer prewarm both fell back (1 of 2 boots).**
     Ollama log 2026-09-27: at the cold boot (12:50:55) the RAG server's bge-m3 warm-up embed took
     **16.4s** (ended 12:51:14), longer than `waitForRagServer`'s 10s cap, so the window opened without
     RAG ready — against bug 62's intent — and the warm-up ran into the boot-video window. The renderer
     prewarm returned HTTP 500 after **4.0s** (aborted by its 4s cap, bugs.md 84). At the warm relaunch
     (13:23) the embed took 0.8s and the prewarm completed in 3.998s — 2ms under the cap. Impact on
     the video is not measured (Zani's check passed that day, boot not identified). **Next step (zero
     code):** read the Ollama log after the next 3 cold boots; the embed duration and prewarm status
     are there. Verdict UNKNOWN until n≥3.
207. **DeepL fallback: alive but never exercised.** `/v2/usage` with `config.json`'s key → HTTP 200,
     `character_count 0 / 500000` (2026-09-27). The key is VALID — REFERENCE.md's "stale" refers to a
     value once listed in the doc, not this key. gemma4 translated 52/52 P1 turns, so the path has run
     0 times this period. UNKNOWN end-to-end. Cheap proof if wanted: one `/v2/translate` call (free
     tier characters, no Fish credit).
208. 🔎 **Now logged in main.log (bugs.md 93).** **Service watchdog respawn (`main.js` `superviseChild`) — UNKNOWN.** Its only output is a main-process
     `console.warn`, which is not kept (#204). No evidence either way. Needs #204.
209. 🔎 **Now logged in main.log (bugs.md 93).** **Page-load retry ×10 (`main.js`, `loadRetries`) — UNKNOWN.** Same reason (#204).
210. 🔎 **Now logged (bugs.md 93) — evidence will accrue in main.log.** **main.js diary-prompt fallback (`diarySystemPrompt || '…'`) — UNKNOWN.** Runs only if the renderer
     omits the prompt. Nothing records which prompt was used. Low risk (bugs.md 57 made the renderer
     always send it). Needs #204.
211. 🔎 **Its console.warn now lands in renderer.log (bugs.md 93).** **Proactive nudge → curated `PROACTIVE_FALLBACK` — UNKNOWN.** No nudge call in the retained Ollama
     log (a nudge is temp 0.9 with a ~4k-token prompt; the only 0.9 call on 09-27 was the 576-token
     diary). Nothing records a curated pick. Needs #204, or a counter in localStorage.
212. 🔎 **Now logged (bugs.md 93).** **`parsEmo` invalid tag → `default` (NOT the previous emotion — corrected 2026-09-27) — UNKNOWN in real use.** No record of how often she
     emits an unknown tag. The probe JSONs in `dev/canon_arms/` could give an offline rate (pure CPU).
213. 🔎 **Its console.warn now lands in renderer.log (bugs.md 93).** **Boot-video blob prebuffer → `amadeus-asset://` src fallback (`amadeus.html`, `playBootVideo`) — UNKNOWN.**
     Console only. Needs #204.
214. **Subtitle `loadedmetadata` → 300ms fallback (`playSyncedAudio`) — UNKNOWN.** Console only.
     **Observe only — the display layer is frozen (CLAUDE.md 51).** Needs #204.
215. **D-Mail curated frame — UNKNOWN (feature unused).** No `amadeus_dmails_v1` key exists, so the
     feature has never run in this profile. Nothing to measure until it is used.
216. ✅ **SHIPPED 2026-09-27 (A + renewal on duplicate/replace/edit; tag `pre-216`). Tone check due when the first note
     appears (~2026-10-27).** **Undated facts never age out and cannot be refreshed.** Raised by Zani 2026-09-27, right after
     bugs.md 92 stored the first facts ever ("Zani is currently coding", egg sandwiches, guitar).
     Exits a fact has: `replaces` (only if the topic comes up again), the 60-fact cap (oldest dropped),
     manual delete in the MEMORY panel, and — for DATED facts only — "N days AGO" labels plus lowest rank
     after 7 days (`_factRank`). An UNDATED fact has no age signal; with ≤20 facts every fact is injected
     whatever its age, so "currently coding" can read as current months later. And a re-mention is
     SKIPPED by the dedupe in `mergeFacts`, so its `date` never refreshes — "confirmed yesterday" and
     "never mentioned again" look the same. Options: (A) derive an age note for undated facts at prompt
     build, like `_factWhen` (bug 64 pattern, no gemma4 call; changes her prompt → his ear, CLAUDE.md 53);
     (B) on a dedupe hit, refresh `date` instead of skipping; (C) tell the extractor to skip transient
     "currently doing" states (prompt change → re-measure). Recommended: A+B, after his step-3 tone check.
     **2026-09-27 measured (dev/facts_arms/PREREG_216.md):** B via a `"confirmed"` output field FAILS —
     gemma4 lists ALL known facts as confirmed (false-confirm rate 1.00 in both mention cells) and a dense
     chat is cut 27/30 at 800. Per the pre-registration: A + refresh on duplicate/replace only, with A worded
     as "learned", not "last mentioned".
217. **`_memoryRefreshActive()` takes the first 20 facts UNRANKED; boot (`initFacts`) ranks them.** Found
     while planning #216. After a memory-panel add/edit/delete, the active set for the rest of that session
     is store order, not `_factRank` order, so a live upcoming exam could fall out if >20 facts exist. Only
     matters above 20 facts (store has 3 today). Fix sketch: call `initFacts()` instead. Small, low risk.
218. **The close-time diary re-index never finishes — it races the quit.** First seen 2026-09-29 in the new
     `renderer.log` (bugs.md 93): `[RAG] diary index skipped: Failed to fetch` at 17:20:59.066, the same
     millisecond as the page's unload lines. `onSaveDiarySummary`'s `finally` calls `indexDiaryInBackground()`,
     but main.js then runs Step 5 and quits, killing the fetch (and the RAG server). Harmless today: the next
     boot's `/index-diary` adds the entry (50/50 entries present on 2026-09-27). A silent fallback that works —
     so it is a clarity issue, not a data loss. Options: drop the close-time call, or let main await it.
219. **Two small log-noise items from the first live logs (2026-09-29).** (1) `main.log` gets one Electron
     warning per launch: `'console-message' arguments are deprecated`, because `attachRendererLog`'s listener
     also accepts the old positional arguments as a backup. The `details` form works (levels are correct in
     `renderer.log`), so the fix is to take only `details` — 1 line in main.js + rebuild; re-run
     `dev/log_sink_test.js` (its positional-shape check changes). (2) At unload the renderer logs
     `BGM track not found: music/believe_me.mp3` and `[BootVideo] error` — teardown clears `src`, which fires
     `error` events. They read like real failures in the log; they are not.
