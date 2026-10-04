# Bugs & Known Footguns — Amadeus Project

**Scope of this file:** isolated crash fixes and "do not reintroduce" entries only.
Architectural rules (TTS pipeline, subtitle sync logic, prosody design) live in `REFERENCE.md` and `CLAUDE.md`.

**Rule: never reintroduce any of these.**

> ⚠️ **Two independent numbering schemes.** `CLAUDE.md`'s "BUGS — DO NOT REINTRODUCE"
> list (1-51, as of 2026-09-07) is NOT the same as this file's entries (1-82, plus 55b and 77b). They collide: e.g.
> CLAUDE.md rule 30 is the boot-video error-listener rule, while bugs.md entry 30
> is the Phase-3 timeout deadlock. Always say which file you mean.
> Known integrity notes: entry 55 appears TWICE (see 55b), and entries here are
> append-ordered, not strictly chronological.

---

## Fixed — Do Not Reintroduce

### 1. DeepL auth method
- **Bug:** DeepL form body auth stopped working (deprecated Nov 2025)
- **Fix:** Use header auth — see `REFERENCE.md` credentials table
- **File:** `kurisu_fish_server.py`

### 2. Ollama CORS in Electron
- **Bug:** `localhost:11434` causes CORS errors in Electron renderer
- **Fix:** Use `127.0.0.1:11434` instead
- **File:** `amadeus.html`

### 3. Fish Audio char_timings null
- **Bug:** Checking `data.char_timings` caused silent failures
- **Fix:** See TTS architecture in `REFERENCE.md` — only `data.audio_b64` is checked
- **File:** `amadeus.html`

### 4. Duplicate const declarations in sendMsg()
- **Bug:** Duplicate `const` declarations crashed entire JS silently — boot video never transitioned
- **Fix:** Audit for duplicate declarations when editing `sendMsg()`
- **File:** `amadeus.html`

### 5. Kanji mispronunciation
- **Bug:** 紅莉栖 kanji mispronounced by Fish Audio
- **Fix:** Always use クリス katakana. Pre-process before API call.
- **File:** `kurisu_fish_server.py`

### 6. parsEmo() tag stripping
- **Bug:** Emotion tags appearing in subtitle text box
- **Fix:** parsEmo() must strip ALL tags — handles both [EMOTION:X] and [X] formats, case-insensitive
- **File:** `amadeus.html`

### 7. Subtitle sync dumping all at once
- **Bug:** All subtitle text appeared instantly instead of word-by-word
- **Fix:** See subtitle sync architecture in REFERENCE.md
- **File:** `amadeus.html`

### 8. playSyncedAudio argument order
- **Bug:** Arguments passed in wrong order caused audio/text mismatch
- **Fix:** Signature is playSyncedAudio(text, audioBase64, emotion) — text FIRST, audio SECOND
- **File:** `amadeus.html`

### 9. parsEmo() destructuring
- **Bug:** Destructured as { emo, text } — wrong key name
- **Fix:** Returns { emotion, text } — use parsed.emotion and parsed.text
- **File:** `amadeus.html`

### 10. Python path in main.js
- **Bug:** Electron doesn't inherit Terminal's PATH — python3 not found
- **Fix:** Hardcode /opt/homebrew/bin/python3
- **File:** `main.js`

### 11. Electron cache stale after edits
- **Bug:** Changes to amadeus.html not reflected after relaunch
- **Fix:** main.js calls session.defaultSession.clearCache() on every launch automatically
- **File:** `main.js`

### 12. isLoading not resetting on error
- **Bug:** If TTS or Ollama errored, isLoading stayed true, locking chat input permanently
- **Fix:** Reset isLoading in finally block, not just on success
- **File:** `amadeus.html`

### 13. parsEmo() space after colon
- **Bug:** Ollama outputs [EMOTION: dismissive] with a space — old regex did not match
- **Fix:** Regex updated to use \s* in three places: parsEmo regex, inner strip, greeting cleaner
- **File:** `amadeus.html`

### 14. wordCount ReferenceError in subtitle sync
- **Bug:** wordCount used inside loadedmetadata callback but never declared
- **Fix:** Declare const wordCount = words.length before the callback
- **File:** `amadeus.html`

### 15. Fragile word split
- **Bug:** text.split(' ') produced empty strings on double spaces
- **Fix:** Use text.trim().split(/\s+/).filter(w => w.length > 0)
- **File:** `amadeus.html`

### 16. Subtitle finishes before audio ends
- **Bug:** Fixed 280ms/word timer ignored actual audio length
- **Fix:** See subtitle sync architecture in REFERENCE.md (audio-duration-based sync via loadedmetadata)
- **File:** `amadeus.html`

### 17. Audible breathing on neutral/calm responses
- **Bug:** [exhale] injected after every ! regardless of emotion
- **Fix:** See prosody architecture in REFERENCE.md (emotion-conditional breath tags)
- **File:** `kurisu_fish_server.py`

### 18. Abrupt tone change between sentences
- **Bug:** Emotion tag only anchored first sentence — Fish Audio drifted to neutral after each pause
- **Fix:** See prosody architecture in REFERENCE.md (EMOTION_ANCHOR re-anchor tags, len(parts) >= 2 guard)
- **File:** `kurisu_fish_server.py`

### 19. import random inside function
- **Bug:** import random was inside compute_speed() — bad practice
- **Fix:** Moved to module top level alongside other imports
- **File:** `kurisu_fish_server.py`

### 20. DeepL API key variable not used in header
- **Bug:** DEEPL_API_KEY variable defined at top of file but actual API call had the old key hardcoded directly as a string in the Authorization header. Rotating the variable had no effect — DeepL auth failed silently and the fallback sent English text to Fish Audio.
- **Fix:** Header now uses f'DeepL-Auth-Key {DEEPL_API_KEY}' — always reference the variable, never hardcode the key string in the header
- **File:** `kurisu_fish_server.py`

### 21. Emotion tag openers vocalised as speech by Fish Audio
- **Bug:** Separate English opener tags ([sharp inhale], [tsk], [gasp] etc.) were prepended before the Japanese text. Fish Audio read them aloud as English speech rather than interpreting them as style instructions, producing audible [warm and genuinely bright...] Hello before the Japanese response.
- **Fix:** Removed separate EMOTION_OPENER prepend from add_prosody_tags(). The emotion character is fully described in the main EMOTION_TAGS entry which immediately precedes Japanese text — one tag, then Japanese, no ambiguity.
- **File:** `kurisu_fish_server.py`

### 22. English bleed in Fish Audio for sentence-grammar emotion tags
- **Bug:** Fish Audio sometimes vocalised English text from emotion tag descriptions instead of treating them as style instructions. Triggered when tag clauses had sentence-like grammar — gerund-start ("speaking slowly with X"), verb-particle endings ("breaking through", "trailing off"), or "as if X-ing" directions. Examples: heard "leaning forward in" and "breaking through" spoken in English on `curious`/`thinking`/`melancholic`/`embarrassed` greetings.
- **Fix:** Rewrote affected tags using fragment grammar (noun phrases, adjective fragments). Tags that were rewritten: `curious`, `thinking`, `melancholic`, `embarrassed`, `blush`. The pattern: replace "voice X-ing Y" with "X-er voice", "speaking slowly with weight" with "slow delivery with weight", etc. Same emotional content, different grammar.
- **File:** `kurisu_fish_server.py`

### 23. parsEmo strict regex letting invented tags leak into subtitles
- **Bug:** Old regex matched only the canonical 20 emotion strings. When gemma4 invented tags like `[concerned]`, `[worried]`, etc., they didn't match and leaked into displayed subtitle text.
- **Fix:** New `validEmotions = new Set([...])` with regex matching ANY `[word]` (no spaces — keeps prose like `[War and Peace]` safe). Strips ALL bracketed tags from subtitle, but only ADOPTS valid emotions; invented ones default to last-known emotion.
- **File:** `amadeus.html`

### 24. Topic fabrication from diary entries injected as memory
- **Bug:** When Phase 1 memory injection started feeding diary entries into the system prompt, gemma4 treated narrative-rich diary phrases ("we discussed pop culture", "she had an essay") as established conversation context. Kurisu would reference essays/manuals/topics that were never actually mentioned by Zani.
- **Fix:** Added "RECENT CONVERSATIONS caveat" paragraph after WHAT YOU KNOW ABOUT ZANI. Tells the model these are private reflections, possibly embellished — treat the EMOTIONAL TONE as memory, not specific topics. Real fix is structural (ABOUT ZANI section with durable facts) so model has actual context to reference instead of imagined ones.
- **File:** `amadeus.html`

### 25. Variant B prompt feminine pronouns for Zani
- **Bug:** Variant B and earlier prompts used she/her for Zani (carried over from drafting assumption). Kurisu would use feminine pronouns for the user.
- **Fix:** Surgical replacement in 4 places in SYSTEM_PROMPT (USER intro, WHAT YOU KNOW section, INPUT→EMOTION line, casual-with-question header). Carefully preserved Kurisu's self-references about original Kurisu (lines 423, 544) and the birthday greeting "before her nineteenth" — those are about Kurisu, not Zani.
- **File:** `amadeus.html`

### 26. Textarea text not clearing after Enter
- **Bug:** Sometimes (intermittent) the input box didn't visually clear after pressing Enter, requiring a second Enter (which sent a duplicate). Caused by macOS autocomplete/IME committing text AFTER our keydown handler ran — the commit re-inserted text after our `value=''` clear.
- **Fix:** (a) Skip Enter handler if `e.isComposing || e.keyCode === 229` (IME composition active). (b) `clearMsgInput()` helper clears synchronously AND schedules a second clear on next tick (`setTimeout(...,0)`) to overwrite any post-handler IME commit.
- **File:** `amadeus.html`

### 27. Ollama spawn ENOENT crash popup
- **Bug:** When Ollama wasn't already running and Amadeus tried to spawn it, `spawn('ollama', ...)` failed with ENOENT because Electron doesn't inherit Terminal's PATH. Threw uncaught exception → popup → app dead. Latent bug exposed by Test 6 (which kills Ollama).
- **Fix:** Hardcoded `const OLLAMA = '/usr/local/bin/ollama'` (same pattern as PYTHON). Wrapped spawn in try/catch + `ollamaProc.on('error', ...)` listener so future failures log to console without crashing app. Path may differ on other systems — `which ollama` to find.
- **File:** `main.js`

### 28. (Phase 3) X-button close path bypassed diary work
- **Bug:** Initial design only handled `app.on('before-quit')` (Cmd+Q path). Clicking the red X close button goes through `mainWindow.on('close')` then `closed`, NOT `before-quit`. Diary work would be skipped on X-button close.
- **Fix:** Added `mainWindow.on('close')` handler that intercepts via `event.preventDefault()` and routes through shared `runDiaryWithExit()` function. Both X-button and Cmd+Q paths now run diary work.
- **File:** `main.js`

### 29. (Phase 3) Double-close race killed save mid-flight
- **Bug:** `diaryHandled` flag was set BEFORE diary work completed. If user clicked close twice quickly during save, second close handler saw `diaryHandled=true` and let window die mid-write.
- **Fix:** Both `mainWindow.on('close')` and `app.on('before-quit')` now check `(diaryHandled && !diaryInProgress)` — only allow close when diary is fully done, not just started.
- **File:** `main.js`

### 30. (Phase 3) Timeout deadlock when Ollama hung
- **Bug:** If 30s race timeout won (because `runDiaryOnClose` was still hung in fetch), `diaryInProgress` was still `true`. When `runDiaryWithExit` called `app.quit()`, the second `before-quit` saw `(true && false)` and prevented quit. App stuck open forever.
- **Fix:** `runDiaryWithExit` now force-clears `diaryInProgress = false` after the race resolves but before calling `app.quit()`. Allows quit to pass guards even if `runDiaryOnClose` is still running its async work.
- **File:** `main.js`

---

## Abandoned Approaches (don't retry without good reason)

### Ollama Translation (Option B)
- Replaced DeepL with an Ollama translation call in kurisu_fish_server.py
- Caused timeouts on cold start — translation model loading competed with chat model
- May revisit with a dedicated tiny model (e.g. gemma3-translator:1b) in future
- Current: DeepL as primary (fast, reliable)

### Fish Speech S2 Local
- Requires ~20GB RAM — Mac has 16GB — MPS out of memory
- Current: Fish Audio cloud API ($11/month, Plus plan)

### 31. (Lip Sync) Cubism 5 SDK parameter scan API broken
- **Bug:** Original code used `core.getParameterId(i)` to scan parameter names → indices for `setParameterValueByIndex`. Cubism Core 5.1.0 (loaded by `live2dcubismcore.min.js`) removes that method on `coreModel`. Scan threw `TypeError: core.getParameterId is not a function`, leaving `window._l2dIdx` null → ticker fell back to `live2dModel.focus()` → blink and lip sync silently broken (head tracking still worked because it was the fallback path).
- **Fix:** Multi-strategy scan tries Cubism 5 paths first then Cubism 4: `core._model.parameters.ids` (raw WASM array of parameter ID strings) → `core._parameterIds` (wrapper cache) → fall back to `core.getParameterId(i)` (Cubism 4). First strategy that yields strings wins. Confirmed by console log: `{ax:0, ay:1, az:2, ex:7, ey:8, bax:32, bay:33, baz:34, el:3, er:5, mouthY:18, mouthForm:17}`.
- **File:** `amadeus.html` (parameter index map IIFE, ~line 1191)

### 32. (Lip Sync) Idle motion overrides direct ticker writes for mouth params
- **Bug:** `setParameterValueByIndex(mouthY, value)` calls in `pixiApp.ticker.add()` were silently overridden every frame because the idle motion (`58Loop.motion3.json`) animates `ParamMouthOpenY`, `ParamMouthForm`, `ParamAngleX/Y/Z`, etc. Pixi-live2d-display's model update runs in its own ticker callback at the same priority and runs the motion AFTER our ticker. Result: mouth visibly didn't move during speech even with correct indices and active analyser data.
- **Fix:** pixi-live2d-display fires `'beforeModelUpdate'` event on `internalModel` AFTER all parameter-modifying systems (motion → expressions → eyeBlink → breath → physics → pose) and BEFORE `coreModel.update()` bakes parameters into the mesh. Listening to that event and writing mouth params there makes our values the *last* writes before render. `live2dModel.internalModel.on('beforeModelUpdate', () => { core.setParameterValueByIndex(idx.mouthY, mo); core.setParameterValueByIndex(idx.mouthForm, formValue) })`. Same approach is required for any other param the idle motion animates.
- **File:** `amadeus.html` (~line 1245, after parameter index map build)

### 33. (Lip Sync) `internalModel.lipSyncValue` does not exist in this build of pixi-live2d-display
- **Bug:** Initial fix attempted to set `live2dModel.internalModel.lipSyncValue = mo` based on the assumption that pixi-live2d-display exposes an external lip sync setter. The build loaded from CDN (`pixi-live2d-display/dist/index.min.js`) only exposes `lipSyncIds` (read from model3.json's LipSync group) and motion-data-driven lip sync via `_lipSyncParameterIds` — there's NO externally drivable lip sync property. The write was a no-op and mouth still didn't move.
- **Fix:** See bug #32 — use the `'beforeModelUpdate'` event on `internalModel` to write mouth params directly. Don't search for or write to `lipSyncValue` — it doesn't exist in this build.
- **File:** `amadeus.html`

### 34. (Lip Sync) AnalyserNode time-domain array sized wrong
- **Bug:** `lipDataArray = new Float32Array(lipSyncAnalyser.frequencyBinCount)` allocates 128 elements (frequencyBinCount = fftSize/2). But `getFloatTimeDomainData()` requires `fftSize` elements (256). With a 128-element array, only half the time-domain window is read each frame, suppressing measured amplitude.
- **Fix:** `lipDataArray = new Float32Array(lipSyncAnalyser.fftSize)` (256). FFT magnitude data uses `frequencyBinCount` (128) — that's the array passed to `getFloatFrequencyData()`. Two arrays, two different sizes.
- **File:** `amadeus.html` (~line 1495 in `ensureAudioContext`)

### 35. (Lip Sync) `pow(x, 0.8)` curve saturated mouthY at 1.0 on every voiced sound
- **Bug:** Output mapping `Math.pow(smooth * AMPLITUDE_GAIN, 0.8)` with GAIN=10 saturated mouthY at 1.0 on any speech (even smooth=0.10 maps to 1.0). The `0.8` exponent is *less than 1*, which means it boosts low values toward 1.0 — exactly the opposite of what was intended. Mouth was effectively a binary on/off, never showing real loudness variation across syllables.
- **Fix:** Linear mapping `Math.min(1, smooth * 3)`. Speech peaks 0.10–0.30 now produce mouthY 0.30–0.90 with occasional 1.0 saturation only on the loudest moments — matches real speech (where /a/ might open ~80% but /i/ only ~30%).
- **File:** `amadeus.html` (`beforeModelUpdate` listener body)

### 36. (Lip Sync) F2/(F1+F2) ratio biased low — all vowels classified as rounded
- **Bug:** Speech inherently has more energy in the F1 band (low frequencies, ~200–1000 Hz) than F2 (~1000–3000 Hz). Raw `highE/(lowE+highE)` ratio for typical Japanese speech clusters around 0.20–0.25, not 0.50. Mapping `(ratio − 0.5) × 2` pushed every vowel to the negative side of the form parameter, including /a/ (which should be neutral). Console showed form values −0.5 to −0.9 dominating, with rare positive spikes.
- **Fix:** Recenter at observed-mean ratio: `(ratio − 0.25) × 3.5`, plus tighten F2 band to bins 7–17 (skip /u/'s borderline F2 ~1100 Hz at bin 6) and reduce analyser `smoothingTimeConstant` from default 0.8 to 0.3 for crisper vowel transitions. Now /a/-spectra land near 0, /i/-/e/ go positive (stretched lips), /u/-/o/ go negative (rounded lips).
- **File:** `amadeus.html` (constants block + `lipTick` formant analysis)

### 37. (Lip Sync) Mouth lingered open after audio ended
- **Bug:** `lipTick` RAF only checked `audio.paused || audio.ended` for fade trigger. Browsers report `ended=true` slightly after the audible signal stops (MP3 trailing silence, decode padding). During that gap the analyser returned zeros, but `lipSyncSmoothed` decayed slowly via `DECAY_FACTOR=0.18` (~600ms tail), keeping the mouth visibly open. Within speech, brief inter-syllable silences also caused the mouth to smear across syllables.
- **Fix:** Two layers: (a) **silence-aware decay** — when `peak < SILENCE_THRESHOLD (0.012)`, switch from `DECAY_FACTOR=0.18` to `SILENCE_DECAY=0.55` (snaps closed in ~14ms) so mouth visibly closes between syllables; (b) **explicit `'ended'` and `'pause'` listeners on the audio element** that immediately call `fadeMouthClosed()` instead of waiting for the next RAF tick to detect it. `MOUTH_FADE_MS` also reduced 150 → 100ms for snappier post-utterance close.
- **File:** `amadeus.html` (`lipTick` body + audio listener wiring in `playSyncedAudio`)

### 38. `process.exit(0)` orphans Electron audio service → AUDIO_RENDERER_ERROR on next launch
- **Bug:** Calling `process.exit(0)` from `mainWindow.on('closed')` (or `window-all-closed`) kills only the Electron main process, leaving child processes — audio service, GPU service — as orphans. The audio service child holds macOS CoreAudio's exclusive device lock. When the next Amadeus launch starts within a few seconds, its audio renderer tries to initialise CoreAudio — still locked — and fails with `AUDIO_RENDERER_ERROR`. This error permanently breaks ALL audio for that Chromium session: boot video audio AND Kurisu's TTS voice are both completely silent, for the entire run.
- **Fix:** Never call `process.exit(0)` from close handlers. Let `app.quit()` → `will-quit` proceed naturally — Electron sends proper IPC shutdown to all child processes before exit, allowing them to release CoreAudio. Add a `will-quit` safety valve: `const t = setTimeout(() => process.exit(0), 5000); if (t && t.unref) t.unref()`. The 5s window is enough for audio service to release CoreAudio; `.unref()` ensures the timer doesn't keep the event loop alive if Electron exits cleanly on its own.
- **File:** `main.js`

### 39. Boot video: `preload="auto"` + `vid.load()` double-load race
- **Bug:** The boot video `<video>` element had `preload="auto"`, which triggers an immediate browser fetch on HTML parse. Then `boot()` called `vid.load()`, which **aborts** the in-flight preload and starts a second fetch. The `loadeddata` event could fire for the aborted first load rather than the new one, causing `playBootVideo()`'s await to resolve with stale state — video never actually began playback, boot transitioned straight to Kurisu with a blank screen. Happened intermittently even on cold boot (no CoreAudio involvement).
- **Fix:** Set `preload="none"` on the video element. Only the explicit `vid.load()` in `playBootVideo()` triggers the fetch, with a single `loadeddata` listener wired up beforehand — one load, one event, no race.
- **File:** `amadeus.html`

### 40. Boot video protocol handler missing HTTP range request support
- **Bug:** The `amadeus-asset://` custom protocol handler read the video file via `fs.readFile()` and returned `new Response(buffer)`. HTML5 `<video>` issues **HTTP range requests** (`Range: bytes=X-Y`) for progressive loading and seeking. A plain `Response(buffer)` sends no `Accept-Ranges` header and can't fulfill range requests — the video element received a non-partial response it didn't know how to use, stalled, and sometimes never loaded at all. This caused intermittent load failures on both cold and warm boots, completely independent of the CoreAudio issue.
- **Fix:** Replace `fs.readFile + new Response(buffer)` with `net.fetch(pathToFileURL(resolved).href, { bypassCustomProtocolHandlers: true })`. Electron's native file fetcher has full HTTP range request support, so `<video>` can stream and seek correctly. Also requires `const { pathToFileURL } = require('url')` import in `main.js`.
- **File:** `main.js` (protocol handler inside `app.whenReady()`)

### 41. Boot video: `error` event listener during playback cut video short
- **Bug:** `playBootVideo()` registered an `error` event listener on the `<video>` element during the playback-wait phase (waiting for `ended`). Any transient audio initialisation hiccup — e.g., a brief CoreAudio recovery moment during early boot — fired an `error` event on the video element. This resolved the wait promise early, cutting the video short mid-play and jumping straight to Kurisu before the `ended` event fired. Result: boot sequence that started normally still truncated.
- **Fix (2026-05):** Remove the `error` listener from the playback-wait phase entirely. Only `ended` + a 14s safety timeout can end the wait (9.78s video + 4.2s headroom).
- **⚠️ SUPERSEDED 2026-08-11 by entry 59 — DO NOT apply this fix to current code.** The premise was that *audio* faults fire `error` on the video element. Entry 59 made the video **permanently muted** (soundtrack moved to a separate `<audio>`), so audio faults can no longer touch it. Current `playBootVideo()` deliberately registers `vid.addEventListener('error', finish, {once:true})` in the playback wait, and that is CORRECT: with a muted RAM-blob source, an `error` there means a genuine visual failure and should end the wait rather than hang for 14s. Verified against source 2026-08-11.
- **File:** `amadeus.html` (`playBootVideo()` function)

### 43. Boot video stops mid-play without recovery when AUDIO_RENDERER_ERROR fires during playback
- **Bug:** Bug 41's fix removed the `error` listener from the playback wait phase to prevent transient audio events cutting the video short. But when `AUDIO_RENDERER_ERROR` fires mid-playback, the video stops (no frames, no audio) and never fires `ended`. The playback wait had no handler — it sat waiting for the full 14s safety timeout. Symptom: video freezes mid-play, boot proceeds 14s later.
- **Fix (2026-05):** Add a one-shot `error` listener that restarts the video muted from the beginning; the handler does NOT resolve the promise.
- **⚠️ SUPERSEDED 2026-08-11 by entry 59 — this recovery machinery no longer exists.** Restart-on-error was a *reactive* patch for a race it kept losing. Entry 59 removed the race at the source by muting the video permanently, so there is nothing to recover FROM. Do not re-add muted-restart logic. Verified against source 2026-08-11.
- **File:** `amadeus.html` (`playBootVideo()` playback wait phase)

### 42. Missing `beforeunload` audio cleanup delays CoreAudio release
- **Bug:** When closing Amadeus, `AudioContext` and `<audio>`/`<video>` elements weren't explicitly released before the renderer process unloaded. The renderer held CoreAudio references that should be released before Electron's child shutdown sequence. This compounded the child-process issue (bug #38) — even with natural Electron quit, the renderer's lingering audio handles slowed CoreAudio release.
- **Fix:** Add `window.addEventListener('beforeunload', ...)` that: pauses and clears `src` on all `<audio>` and `<video>` elements, and calls `audioCtx.close()` if the context isn't already closed. Belt-and-suspenders with the natural Electron quit sequence — both renderer and audio service release CoreAudio cleanly.
- **File:** `amadeus.html`

### 44. `did-fail-load` retries discard `?incomingCall=1` URL param
- **Bug:** `createWindow()` builds `htmlUrl` and immediately calls `mainWindow.loadURL(htmlUrl)`. The `did-fail-load` handler was registered as `() => setTimeout(() => mainWindow.loadURL(newUrlBuiltHere), 1500)` — rebuilding the URL from scratch each retry. If the first load failed (server not yet up), the retry silently dropped `&incomingCall=1`, and the special incoming-call greeting never triggered.
- **Fix:** Capture `const htmlUrl = ...` as a closure variable before registering `did-fail-load`. The handler closure captures `htmlUrl` at registration time — every retry reuses the same complete URL including the `incomingCall` param.
- **File:** `main.js`

### 45. Unused `session` import in main.js
- **Bug:** `session` was destructured from `require('electron')` but never referenced — leftover from the `session.defaultSession.clearCache()` feature that was removed. Harmless but untidy; could confuse future audits.
- **Fix:** Removed `session` from the electron destructure.
- **File:** `main.js`

### 46. `ttsProcess` spawn missing error handler
- **Bug:** `ttsProcess = spawn(PYTHON, [...])` had no `.on('error', ...)` listener. If `kurisu_fish_server.py` could not be found or executed (wrong path, permission error, Python missing), Node.js emitted an unhandled `'error'` event on the child process — crashing main.js with an uncaught exception and killing the entire Electron app.
- **Fix:** Added `ttsProcess.on('error', (err) => console.warn('[main:tts] spawn failed:', err.message, '- TTS unavailable this session'))`. Matches the pattern already on `ragProcess` and `whisperProcess`. TTS unavailability is logged, not fatal.
- **File:** `main.js`

### 47. AmadeusCall `second-instance` fires before `app.whenReady()` — BrowserWindow crash
- **Bug:** The `second-instance` handler in `scheduler/main.js` called `fireIncomingCall()` unconditionally when `--test-call` was in argv. `fireIncomingCall()` calls `createCallWindow()`, which calls `new BrowserWindow()`. Electron does not allow BrowserWindow construction before `app.whenReady()` resolves — if a second instance connected during startup, the handler fired immediately and crashed with `Error: BrowserWindow cannot be created before app is ready`.
- **Fix:** Added `let appReady = false` module-level flag. Set to `true` at the very start of `app.whenReady().then(...)`, before any `fireIncomingCall()` call. The `second-instance` handler now guards with `if (appReady) fireIncomingCall()`.
- **File:** `scheduler/main.js`

### 49. `preloadModel()` missing `think: false` + redundant with `prewarmOllama()`
- **Bug:** `preloadModel()` (fired at every page load) sent an `api/chat` call without `think: false`, violating bug 13. With gemma4 thinking mode enabled, this could return empty or malformed content. Additionally, after `prewarmOllama()` was introduced (May 15, 2026), both functions loaded gemma4 simultaneously — redundant and wasteful. `preloadModel()` also fired at page load before Ollama was ready, requiring a 45s polling loop with 3s intervals, and unnecessarily disabled the send button during boot.
- **Fix:** Removed `preloadModel()` entirely. `prewarmOllama()` (fires during greeting TTS dead time, has `think: false`, 30s timeout, fire-and-forget) fully supersedes it. Send button no longer disabled during boot — boot video and greeting take ~10s before the chat UI is visible anyway.
- **File:** `amadeus.html`

### 50. `serverProcess` (http.server) missing `.on('error', ...)` handler
- **Bug:** `serverProcess = spawn(PYTHON, ['-m', 'http.server', '8765'])` had no error listener. All other spawned processes (`ollamaProc`, `ttsProcess`, `ragProcess`, `whisperProcess`) had `.on('error', ...)` handlers. If Python couldn't be found or the port was in use, an unhandled `'error'` event on the child process would crash main.js with an uncaught exception popup. Same class as bug 46.
- **Fix:** Added `serverProcess.on('error', (err) => console.warn(...))` immediately after the spawn call. Matches the pattern used by all other child processes.
- **File:** `main.js` (rebuild required)

### 48. Scheduler timer drifts on macOS sleep; multiple timers stack on hourly checks
- **Bug (drift):** The original `scheduleNextDayCheck()` set a single `setTimeout` to midnight. macOS pauses the monotonic clock during system sleep — a Mac asleep for 8 hours would fire the timer 8 hours late. The call could silently miss its window.
- **Bug (stacking):** `scheduleCall()` was called once at boot and once at midnight by `scheduleNextDayCheck()`. There was no guard preventing multiple timers. Any code path that called `scheduleCall()` twice before the scheduled time would arm two independent timers, both firing at the target minute and opening two simultaneous call windows.
- **Fix (drift):** Replaced `scheduleNextDayCheck()` with `scheduleHourlyCheck()` — a recursive `setTimeout(1 hour)` loop that calls `scheduleCall()` on each tick. Limits sleep/wake drift to ≤1 hour.
- **Fix (stacking):** Added `let callTimerSet = false` flag. `scheduleCall()` checks it before arming a new timer (`if (callTimerSet) return`). The timer callback resets it to `false` when it fires, so tomorrow's first `scheduleCall()` invocation can arm a new timer. `scheduleCall()` is now fully idempotent.
- **File:** `scheduler/main.js`

### 22a. Acoustic-anchor rule for EMOTION_TAGS (addendum to bug 22, May 16 2026)
- **Rule:** Every comma-fragment inside an EMOTION_TAG must end in an acoustic or physical anchor noun — `quality`, `brightness`, `edge`, `lift`, `pace`, `intensity`, `texture`, `delivery`, `voice`, `pitch`, `form`, `weight`. Fish Audio recognises these as voice-direction vocabulary and never speaks them. Fragments describing a pure internal mental state with no acoustic referent will be vocalised. Trailing adverbs (`throughout`, `always`, `constantly`) are the strongest signal that a fragment reads as a complete statement — avoid them.
- **Latest instance:** `curious` tag had `genuine engaged interest throughout` → replaced with `intent investigative edge` (adjective + adjective + anchor noun).
- **File:** `kurisu_fish_server.py`

### 51. Ollama KV cache not reused — `num_ctx` mismatch between prewarm and sendMsg()
- **Bug:** `prewarmOllama()` sent no `num_ctx` option (Ollama default: 2048). `sendMsg()` sends `num_ctx: 8192`. Ollama allocates a KV buffer sized to `num_ctx` — different sizes = different buffer = cache miss guaranteed. Every first message forced Ollama to reallocate, discarding the prewarm. Symptom: first-message lag persisted even after prewarm was introduced.
- **Fix:** Added `num_ctx: 8192` to `prewarmOllama()`'s options, matching `sendMsg()` exactly. Also replaced the `'hi'` message with `buildSystemPrompt('')` so the full system prompt prefix is cached before the user types.
- **File:** `amadeus.html`

### 52. main.js prewarm racing the renderer's prewarm and evicting KV cache
- **Bug:** `prewarmOllamaMain()` sent a bare `'hi'` request (no system prompt, no `num_ctx`). If it arrived after the renderer's system-prompt prewarm, Ollama overwrote the useful KV cache. Both requests competed destructively regardless of order.
- **Fix:** AbortController bound to the 5s window delay — `prewarmAbort.abort()` fires before `createWindow()` opens. Main's prewarm is guaranteed cancelled before the renderer fires. No stale request can arrive after window open.
- **File:** `main.js`

### 53. `strip_unsafe_tags` silently stripping all EMOTION_TAGS before Fish Audio
- **Bug:** `kurisu_fish_server.py` had a `strip_unsafe_tags()` function with a small `_SAFE_TAGS` whitelist of short prosody tags. EMOTION_TAGS (the primary voice direction mechanism) were not in the whitelist and were silently stripped before every Fish Audio API call. Result: Fish Audio received plain Japanese text with no voice direction, producing universally dull, flat, slow-paced output regardless of emotion.
- **Fix:** Removed `strip_unsafe_tags` and `_SAFE_TAGS` entirely. The Fish Audio call now passes the full tagged text directly — `f"{EMOTION_TAGS[emotion]} {japanese_text}"`. No filtering.
- **File:** `kurisu_fish_server.py`

### 55. Boot video freezes mid-play when muted restart also fails
- **Bug:** When `AUDIO_RENDERER_ERROR` fired mid-playback, the error handler restarted the video muted. Two sub-bugs caused the video to freeze: (a) `vid.play().catch(()=>{})` — if the muted restart's `play()` also rejected, the error was swallowed silently and the video stopped, waiting the full 12s timeout before boot continued. (b) `{once:true}` on the error listener — if a second error fired during the muted replay, it went unhandled, freezing the video again with no recovery path. User saw the video stop mid-play then boot continue ~12s later.
- **Fix:** Kept `{once:true}` on the outer handler (critical — `vid.play()` on an errored element fires a second error synchronously, which without `{once:true}` re-triggers the handler before the muted replay starts, causing immediate `finish()`). Fixed `.catch(()=>{})` → `.catch(()=>{ finish() })` so a rejected muted `play()` fails fast. Added a 300ms-delayed second one-shot error listener for genuine errors during the muted replay, after side-effects from `currentTime=0` and `play()` have cleared.
- **File:** `amadeus.html`

### 54. Fish Audio phoneme loop from `repetition_penalty 1.1`
- **Bug:** `repetition_penalty: 1.1` in the Fish Audio API call caused the TTS to enter a phoneme loop — a single word or sound repeated continuously, producing broken audio far longer than the intended response. Also caused text streaming to lag severely.
- **Fix:** Revert `repetition_penalty` to `1.2`. 1.1 is too close to 1.0 for Fish Audio S2 Pro and triggers the loop on certain phoneme sequences. 1.2 is the stable value.
- **File:** `kurisu_fish_server.py`

### 55b. Relationship directive MUST be frozen at boot (KV-cache prefix discipline)
*(Numbering collision: a different bug also claims 55 above. Kept as 55b — renumbering would break existing references.)*
- **Rule:** The relationship-stage directive injected by `buildSystemPrompt()` must be byte-identical for the entire session. The active stage is frozen once in `initRelationship()` (which runs BEFORE `prewarmOllama()`); only `_relActiveStage` is read by `relationshipDirective()` all session. The score keeps growing live, but the stage must NOT re-read mid-session.
- **Why:** `prewarmOllama()` caches the full system-prompt prefix during boot. If the directive text changed mid-session (e.g. recomputing stage from the live score), the cached KV prefix would no longer match `sendMsg()`'s prompt → cache miss → first-message-class prefill cost on every turn (re-introduces the bugs 33/34 class of lag). Inject the directive in the static body BEFORE the RAG tail so the prefix stays stable.
- **File:** `amadeus.html` (`initRelationship`, `relationshipDirective`, `buildSystemPrompt`)

### 56. Incoming-call paths must write `amadeus_last_seen`
- **Bug:** Only `pickGreeting()` wrote `amadeus_last_seen`. The incoming-call boot path (`?incomingCall=1`) and the in-session incoming-call handler bypassed `pickGreeting()`, so accepting a call left `last_seen` stale. Broke both tiered absence greetings AND the relationship arc's reunion-coolness detection.
- **Fix:** Write `localStorage.setItem('amadeus_last_seen', String(Date.now()))` (wrapped in try/catch) in BOTH the incoming-call boot path and the in-session incoming-call handler.
- **File:** `amadeus.html`

### 57. Diary stage prompt — renderer is source of truth, main.js needs a fallback
- **Rule:** Diary generation runs in TWO places: `generateDiaryEntry()` (renderer) and the diary-on-close coordinator (`main.js`, which runs Ollama itself). The stage-aware diary prompt is built by `buildDiarySystemPrompt()` in the renderer. The renderer passes it to main.js via the `conversation-response` IPC payload (`diarySystemPrompt`); `main.js` MUST keep its own hardcoded fallback string (`diarySysContent = diarySystemPrompt || '...'`) in case the renderer ever omits the key, otherwise an old renderer + new main = `undefined` system prompt.
- **Note:** `main.js` requires `npm run build` after edits; `amadeus.html` and `preload.js` (which forwards the payload verbatim) do not need it here, but `preload.js` does need a rebuild if its channels change.
- **File:** `amadeus.html`, `main.js`

### 58. Boot video regression — src assignment + load() = double load-algorithm invocation
- **Bug:** The greeting-cache era blob prebuffer set `vid.src=_bootVideoBlobUrl` at `playBootVideo()` entry, then the play loop called `vid.load()`. Assigning `src` *itself* invokes the HTML media load algorithm, so the explicit `load()` aborted an in-flight load and restarted it — bug 28's double-load race reintroduced through a different door. Symptom: video intermittently never played, or stopped mid-play (July 13, 2026).
- **Fix:** Exactly ONE load invocation per attempt: swap to the blob src (implicit load) when the prebuffer is ready and not yet applied, otherwise plain `vid.load()` on the current src — never both, listeners attached first. Same pattern in the bug-55 mid-play recovery, which now also prefers the RAM blob (immune to disk contention). Media event sequence logged to console (`[BootVideo]`) for future diagnosis.
- **File:** `amadeus.html` (`playBootVideo`)

### 59. Boot video: decouple the VISUAL from the audio device (supersedes 41/43/55)
- **Bug:** The video stalled at the same point on nearly every boot ("right before the logo"). Diagnosed 2026-07-21 from the `[BootVideo]` event trail plus the main-process log: the audio device layer was failing during boot (`"The AudioContext encountered an error"`, repeated `MixableOutputStream: Error during independent playback`), and because the `<video>` element was UNMUTED it was welded to that same audio renderer. **The visual was dying for an audio reason.** Entries 41, 43 and 55 were all reactive patches trying to detect and recover from that failure after the fact — they kept losing the race by design.
- **Fix:** Structural, not reactive. The boot `<video>` is now **permanently muted** (`vid.muted=true`), which makes muted playback never touch the audio device at all — the visual becomes immune to the entire CoreAudio/audio-renderer failure class. The soundtrack plays on a SEPARATE `<audio>` element that **fails soft**: a broken audio stack yields a silent boot video that still completes, never a frozen one. Consequently the playback wait now legitimately registers `vid.addEventListener('error', finish, {once:true})` — with a muted RAM-blob source, an `error` there means a real visual failure and should end the wait rather than hang for 14s. All the muted-restart recovery machinery from 43/55 was deleted.
- **Also fixed here:** the `amadeus-asset://` handler's `try/catch` only covered the SYNCHRONOUS path — `net.fetch` returns a promise that REJECTS on a missing file (e.g. a greeting-cache miss), surfacing as an unhandled `net::ERR_FILE_NOT_FOUND` instead of a clean 404. Now caught on the promise.
- **Rule:** Do NOT unmute the boot video element to "restore boot sound" — that reintroduces 41/43/55/59. The soundtrack belongs on its own element. (CLAUDE.md rule 38.)
- **Verified:** post-fix `[BootVideo]` trail showed `playing t=0.00 → ended t=9.80 rs=4`, full playback, no `error`/`waiting`.
- **File:** `amadeus.html` (`playBootVideo()`), `main.js` (protocol handler)

### 60. Boot video decoder stalls from heavy work running DURING playback
- **Bug:** The boot video's decoder stalled mid-playback (readyState 4→2 on a RAM-blob source = pure CPU/decode starvation, not I/O), most visibly at t≈8.6s "right before the logo". Instrumented via the [BootVideo] event trail (July 21, 2026). Cause: prewarmOllama() and the greeting-audio prefetch were fired BEFORE playBootVideo() to "use the video window" — but the greeting cache-miss path now runs a gemma4 register-aware translation AND a large IPC audio cache-write, and prewarm runs a gemma4 KV prefill, all landing mid-video and starving the decoder.
- **Fix:** Defer prewarmOllama() AND fetchGreetingAudio() to AFTER playBootVideo() (normal boot path). The ~10s video decodes on an idle system; warming after it still finishes long before the user can type (fade + Live2D init + greeting playback ≈ 12s runway). Cache-miss greetings may trail the reveal by a second or two — acceptable, the uninterrupted video is the priority. The incoming-call path already prewarmed after reveal (no video there).
- **File:** `amadeus.html` (`boot`, normal path)

### 61. Background gemma4 work stutters Kurisu's animation (shared GPU) and slows replies
- **Bug:** After the July 18 translator swap (DeepL → gemma4) and the July 25 greeting warmer, Zani reported new lag: Kurisu's Live2D movement stuttering, and delays before/during her replies. Diagnosis: `ollama ps` shows gemma4 runs **100% on GPU**, and Live2D/PIXI renders via WebGL on that same GPU — so every gemma4 inference steals GPU from her animation. Measured 0.66s of saturation per translate call. The greeting warmer called `/speak`, which now routes through the gemma4 translator, at up to 35 calls × 5s gaps behind only a 20s idle gate → ~23s of GPU saturation across the first 3 minutes of every boot, firing while Zani was reading replies, and evicting the chat KV prefix each time (+0.57s on his next message — **that +0.57s was re-measured on 2026-09-07 and is now +2ms on Ollama 0.33.3; the July figure was wall time of a 3-token request, not prefill. See backlog #196. The GPU-saturation half of this bug is unaffected and still stands.**). Facts extraction (every 6th exchange) fired immediately for the same reason.
- **Fix:** Background gemma4 work now runs ONLY when the GPU is genuinely free, and yields instantly. Greeting warmer: 10/session (was 35), 15s gaps (was 5s), 3-min idle gate (was 20s), also allowed when `document.hidden` (PIXI ticker is stopped then — the ideal window), and its fetch is abortable — `noteActivity()` cancels it on any interaction. Facts extraction: deferred to the next lull (45s idle or hidden) instead of firing mid-conversation. Gate logic unit-verified live.
- **Rule:** ANY new background gemma4 caller must be idle-gated AND abortable. Never fire inference speculatively while the user may be interacting.
- **File:** `amadeus.html` (`_warmIdle`, `warmGreetingCache`, `noteActivity`, `maybeExtractFacts`, `_factsIdleOk`)

### 62. Cold-start lag: prewarm colliding with Live2D, RAG spawning too late
- **Bug:** After bugs 60/61, two lag points remained (Zani, July 29): Kurisu **stuttering as she appears**, and a slow **first reply**. Causes: (a) the bug-60 fix moved `prewarmOllama()` to just after the video, which put gemma4's 1-3s 100%-GPU KV prefill directly on top of `initLive2D()`'s WebGL model/texture upload — they fought for the GPU at exactly her entrance; (b) the RAG server spawned 20s AFTER the window opened and needs ~10s to warm, so the first message burned `fetchRagContext`'s full 4s timeout against a server that wasn't up; (c) bge-m3 was evicted after diary indexing, costing a 1-2s reload on the first RAG query.
- **Fix:** `prewarmOllama()` now runs AFTER `initLive2D()` (reveal + greeting give ~10s runway, so it's still warm before the user can type). RAG is spawned in the **pre-window phase** and the gate is adaptive — `Promise.all([http, waitForRagServer(), min 5s])` — so its GPU-heavy warm-up finishes before the window opens, protecting the boot video (bug 60) while being genuinely ready for message 1. `waitForRagServer` is self-bounded (10s → false), so a broken RAG can never block launch. The server only serves `/health` after warm-up completes, so a healthy response is a true readiness signal. bge-m3 eviction removed (measured ~72% memory free — it bought nothing and cost a reload). Added a RAG **circuit breaker**: after a failure, retrieval is skipped for 60s, so a dead server costs 4s once per minute instead of 4s per message.
- **Rule:** GPU-heavy work (model prefill, RAG/bge-m3 warm-up) must never overlap the boot video OR Live2D init. Do it in the pre-window phase or after the reveal.
- **File:** `main.js` (pre-window gate, `spawnRagServer`), `amadeus.html` (`boot`, `indexDiaryInBackground`, `fetchRagContext`)

### 63. Greeting never entered history (tonal + content discontinuity) + reveal stutter from greeting cache miss
- **Bug A (behaviour):** The boot greeting was spoken via `ttsGreeting()` but **never pushed into `history`** — the only utterance type that wasn't (canon lines, proactive nudges, D-Mail deliveries, study remarks and birthday gifts all were). So on the first message the model saw an EMPTY conversation and replied as if Zani had just walked in. Reported July 29: she greeted him warmly, he replied "Hello, long time no see", and she answered "Hey, you showed up... What do you want?" in a flat tone — both jarring content and a jarring tonal shift. A/B reproduced it exactly ("Oh. You showed up." / "look who finally decided to grace me with his presence") and confirmed the fix ("Don't get the wrong idea; I wasn't expecting to hear from you at all. What have you been up to?").
- **Fix A:** Push the greeting into `history` as `[EMOTION:x] text` in all three greeting paths (normal boot, `?incomingCall=1` boot, and the already-open incoming-call IPC). Also softened the prompt's bare "Vary emotions across turns" — shifts must now be MOTIVATED by what he just said, with an explicit instruction not to reset to a distant "what do you want" after a warm greeting.
- **Bug B (performance):** 2-3s stutter right after Kurisu appears. Cause: only the generic + current time-of-day greeting pools had ever been warmed, so an **absence-tier greeting** (which is exactly what fires after a gap — the "long time no see" case) was a cache MISS, costing a gemma4 translation (0.85s) + Fish synthesis (1.27s) of GPU work landing on her reveal. Bug 62's prewarm placement (right after `initLive2D`) compounded it.
- **Fix B:** (1) All 88 greetings across all 14 pools warmed offline, including absence tiers, birthdays and incoming-call. (2) `boot()` now checks the cache first: a HIT prefetches immediately (cheap disk read), a MISS passes no promise so `ttsGreeting()` synthesises AFTER the reveal — expensive work can never stutter her entrance; worst case she takes a breath before speaking. (3) `prewarmOllama()` moved to `await Promise.race([prewarmOllama(), delay(4000)])` BEFORE the video — awaited to completion (NOT fire-and-forget, which is what bug 60 forbade), so the video, Live2D init, reveal and greeting all get an idle GPU.
- **Rule:** Any new utterance Kurisu speaks MUST be pushed to `history`, or she will not know she said it.
- **File:** `amadeus.html` (`boot` both paths, `onIncomingCallAccepted`, SYSTEM_PROMPT emotion-tag section)

### 64. Memory had no temporal grounding — stale facts asserted as upcoming
- **Bug:** Zani observed Kurisu still asking about exams that were already over. Three compounding causes: (a) **she had no clock** — `formatTimeContext()` returned '' outside 01:00-05:00, so for 20 hours a day she did not know the date and literally could not tell that a dated event had passed; (b) **facts had no event date** — the store recorded only when a fact was *learned*, so "physics exam on 4 August" was structurally indistinguishable from "likes teal"; (c) the SYSTEM_PROMPT hardcoded "care about his day, meals, sleep, and **exams**" as a permanent standing instruction. Reproduced: with a 7-day-past exam in memory she replied "A physics exam, right? You have one coming up on the 4th of August."
- **Also found:** the facts store had **never been written** — zero facts in the 9 days since the feature shipped, because extraction required 6 exchanges in ONE session *and* (since bug 61) 45s of idle. The mechanism itself worked fine when tested directly; the trigger was simply unreachable in ordinary use.
- **Fix:** (1) `formatTimeContext()` now always states today's date + weekday (changes once per day, so the prompt stays byte-identical within a session — KV discipline intact). (2) Facts gained an `event_date`, captured at extraction (which is now told today's date so it can resolve "Friday"/"next week"). (3) Temporal position is **DERIVED at prompt-build time** by `_factWhen()` comparing `event_date` to local midnight — "[in 3 days]" / "[7 days AGO — already happened; asking how it went is natural]". Derived rather than stored, so it can never go stale and needs no periodic reconciliation pass. A passed event is not deleted; it becomes shared history. (4) Extraction may now **invalidate** a known fact via `replaces` when the conversation contradicts it — event-driven, cheaper and more timely than polling. (5) Extraction trigger relaxed to a 2-exchange minimum, with the idle gate alone deciding when it runs. (6) The hardcoded "exams" instruction replaced with "whatever he currently has on", plus an explicit rule never to raise a commitment that is already past.
- **Bonus bug caught while testing:** every date the memory/D-Mail layers wrote used `toISOString().slice(0,10)` = **UTC**, while `_factWhen` compares against **local** midnight. In BST (UTC+1) that mis-dates everything written between 00:00-01:00 local by a full day, and disagreed with the comparison logic. All six call sites now use a shared `_localDateStr()`.
- **Rule:** any date the app persists or shows the model must be LOCAL (`_localDateStr()`), never `toISOString()`.
- **File:** `amadeus.html` (`formatTimeContext`, `formatFactsSection`, `_factWhen`, `_localDateStr`, `extractFactsNow`, `mergeFacts`, `maybeExtractFacts`, D-Mail helpers, SYSTEM_PROMPT)

### 65. Diary voice collapsed into one template and one emotional register
- **Bug:** Audit of 35 real diary entries found 25 (71%) opened with the single word "Honestly," with heavy reuse of "exhausting" (x8), "frankly" (x10), "suppose" (x11). Separately, 31/35 (88%) contained complaint vocabulary against only 13/35 (37%) containing warmth. Verified NOT a feedback loop — buildDiarySystemPrompt never shows past entries, yet 3 of 5 fresh generations with an empty history still opened "Honestly,". It is an intrinsic gemma4 mode for "private tsundere diary". The monotone matters beyond the diary: the 7 latest entries inject into EVERY session as RECENT CONVERSATIONS, so a wall of complaint quietly biases her live conversational persona toward dismissiveness — the opposite of canon, where the private diary is exactly where warmth under the prickliness should show.
- **Fix:** Two patterns already proven in this codebase. (1) A rotating structural ANGLE per entry via pickFresh over DIARY_ANGLES (the PROACTIVE_MODES pattern) — fixate on one thing he said / notice your own reaction / start mid-thought / record an ordinary detail / admit what you would not say aloud / note what you enjoyed / be brief and dry / write what you held back. (2) An avoid-list built from the REAL store: the first two words of the last 6 entries are passed in and forbidden (the pickFresh anti-repeat principle applied to prose). Plus an explicit ban on "Honestly"/"Frankly" and a tone-rebalance line stating irritation is only one register among amusement, curiosity, reluctant fondness and plain observation.
- **Verified:** 6 fresh generations gave 0/6 "Honestly" openers and 6/6 unique openings, with visibly wider emotional range.
- **Note:** main.js keeps its own hardcoded fallback diary prompt (bug 57) which does NOT rotate — it is only used if the renderer fails to send one.
- **File:** `amadeus.html` (`DIARY_ANGLES`, `buildDiarySystemPrompt`)

### 66. Lip-sync `MediaElementSource` nodes accumulated for the whole session
- **Bug:** `playSyncedAudio` calls `audioCtx.createMediaElementSource(audio)` once per reply and connects it to the persistent `lipSyncAnalyser`. Nothing ever disconnected it. The graph is `source → analyser → destination`, so every node stayed referenced by the analyser for the life of the session — one per reply, forever. A slow leak, worse the longer a session ran, and it would have been 3-5x worse under sentence pipelining (backlog #153).
- **Fix:** an idempotent `teardownLipSource()` inside the same `try` block, called from the existing `onAudioStop` handler after `fadeMouthClosed()`. A `lipTornDown` flag makes it safe for `'ended'` and `'pause'` both firing on the same element.
- **Rule — do NOT disconnect an element that could play again.** Her voice routes THROUGH this node, so disconnecting a live element makes her silent. This fix is only safe because it was verified that nothing resumes a reply element: the only three `pause()` calls on `currentAudio` (`amadeus.html` ~1739, ~1851, ~3553) all abandon it, and the window-hidden throttle pauses `bgmAudio` only. If a pause/resume path is ever added, this teardown must move to an explicit abandonment point.
- **Rule preserved:** bugs.md 26/37's explicit `'ended'`/`'pause'` mouth-close must still run FIRST — teardown is appended after `fadeMouthClosed()`, never in place of it.
- **Verified live (Aug 18, 2026):** Zani relaunched and confirmed her voice plays normally and her mouth moves and closes normally. That was exactly the failure this rule guards against, so the fix is confirmed in the real app, not only by reasoning.
- **File:** `amadeus.html` (`playSyncedAudio` lip-sync wiring)

### 67. A truncated reply was spoken AND written into memory
- **Bug:** `num_predict:120` caps generation. On a cap-hit Ollama ends the stream with `done_reason:'length'` and the reply simply stops mid-sentence. `ollamaStream` read only `message.content` and `obj.done` — never `done_reason` — so a cut-off reply was indistinguishable from a finished one. The fragment was translated, spoken by Fish Audio, and pushed into `history` as her canonical utterance, from where it feeds the diary generator and the fact extractor. **A truncation became permanent memory.** ACADEMIC mode (≤70 words plus the emotion tag) is the most exposed.
- **Verified live** against Ollama 0.21.0 before building: a streaming request with `num_predict:1` returns `"done":true,"done_reason":"length"`; a natural end returns `"done_reason":"stop"`. The contract is real, not assumed. **Re-verified on Ollama 0.32.15 (2026-08-26)**, and additionally for the NON-streaming (`stream:false`) `/api/chat` shape used by main.js — `done_reason` sits at the top level of the response object there. Contract unchanged across both versions.
- **Fix:** `ollamaStream(body, onToken, retries, meta)` takes an optional out-parameter and sets `meta.doneReason` on the final chunk. An out-param rather than a changed return type keeps the existing string contract; rather than a module-level variable so two concurrent callers cannot read each other's result. `sendMsg` then trims to the last complete sentence via `trimToLastSentence()`, and pushes the TRIMMED text to history so memory matches what she actually said.
- **Deliberate limit:** trimming is skipped when it would leave under 20 characters or under 40% of the reply — a fragment she says is better than losing most of her answer. Unit-tested 9/9 against the shipped function.
- **Normal path is byte-identical.** The guard only acts on `done_reason==='length'`; the untruncated `history.push` line is unchanged.
- **Known remaining gap:** the proactive-nudge, canon-remark and birthday paths call `/api/chat` directly with `stream:false` and are NOT yet guarded. Same class of defect, smaller blast radius. Tracked in improvements-backlog #159.
- **Dev:** `truncStatus()` in DevTools returns `{cutOff, replies, rate}` for the session.
- **File:** `amadeus.html` (`ollamaStream`, `trimToLastSentence`, `sendMsg`)

### 68. The volatile RAG block sat ahead of the whole history and destroyed the KV cache
- **Bug:** `sendMsg` built `[{system: buildSystemPrompt(ragCtx)}, ...history]`, and `buildSystemPrompt` appended the retrieved RAG lines to the END of the system message — which is the START of the token sequence. The retrieved lines differ every turn, so the prefix shared with the previous turn ended there, and the RAG tail **plus the entire 30-message history** was re-prefilled on every single message. All the KV discipline of bugs 33/34/51/52/55b (freezing the relationship stage, freezing facts at boot, keeping time context stable within a day) protected the static body — and then this placement threw the rest away.
- **Measured before building, on this machine** (`dev/` scratch harness, 5 reps, ~5,060-token prompt, gemma4): volatile-tail-in-system **672 ms** median prefill per turn (663-695) vs. RAG-as-its-own-message-before-the-user-turn **176 ms** (173-177). **~496 ms saved per turn**, and the gap widens as history grows.
- **Metric warning:** `prompt_eval_count` is NOT a cache-miss indicator — it reports TOTAL prompt tokens and read ~5,060 in every condition, cached or not. Only `prompt_eval_duration` reveals prefix reuse. An earlier note in improvements-backlog #154 claimed otherwise; corrected.
- **Fix:** `RAG_AS_TAIL_MESSAGE = true` (beside `HISTORY_WINDOW`). `sendMsg` calls `buildSystemPrompt(null)` and splices the retrieved block in as its own `system` message immediately before the current user turn (`_msgs.splice(_msgs.length-1, 0, ...)`). The one-shot memory-panel note moved with it — same class of per-turn content. Set the constant to `false` to restore the old layout instantly.
- **Placement verified:** message order is `system → …history… → system(RAG) → user(current)`, and the current user message stays last so the vision image-attach line still targets it. Empty-history and greeting-in-history cases both produce correct order.
- **Behaviour verified:** gemma4 respects a mid-list system message — a live probe returned an in-character, correctly tagged, 12-word reply that used the retrieved STYLE while borrowing none of its topics (the bleed risk the block's own header warns about).
- **Telemetry:** `notePrefill()` logs `[Prefill] N ms for T prompt tokens` each turn; `perfStatus()` in DevTools returns turns/median/min/max. Turn 1 is always high (nothing cached); judge from turn 2. A median near the turn-1 figure means something has re-entered the system message and the prefix is being invalidated again.
- **Rule:** nothing that changes per turn may live in the system message. (CLAUDE.md 41)
- **File:** `amadeus.html` (`RAG_AS_TAIL_MESSAGE`, `sendMsg`, `ollamaStream` meta, `notePrefill`, `perfStatus`)

### 69. Her diary was written in lab prose, and she quoted it back verbatim
- **Bug:** `buildDiarySystemPrompt()` instructed *"precise, slightly tsundere"* and carried **no vocabulary constraint at all**, while her SPEECH has the full CASUAL WORD RULE with a banned list. So diary entries were generated in clinical prose — *"his 'biological hardware'"*, *"threw my processing unit into an inefficient state"*, *"a basic physiological requirement"*. Those entries are then injected into every later prompt as **"in your own past words"** (RECENT CONVERSATIONS) and retrieved by RAG as RELEVANT PAST MOMENTS. She modelled her voice on them and **quoted them verbatim, quote marks included**: *"Don't mess up your 'biological hardware'"*, *"running low on processing power"*. A feedback loop: clinical diary → clinical replies → clinical diary.
- **Found:** from Zani's `dumpLastTurn()` capture (Aug 23) after he flagged the reply *"Don't let your biology run down."* That turn's retrieved block contained *"a basic physiological requirement"* and the memory window contained *"biological hardware"*.
- **Consumption side — PROVEN.** Topic-matched probes (meals/sleep/care, the topics those entries cover): clinical memory produced **5/36 (14%)** clinical replies; the SAME memories rewritten in plain words produced **0/36 (0%)**. Fisher exact one-sided **p = 0.027**.
- **Why off-topic probes miss it:** an earlier run using swimming/rain/cats found nothing (0/24, 0/24) because RAG never retrieves the clinical entries for unrelated topics. **An off-topic probe set cannot test a topic-triggered retrieval effect** — that is the methodological lesson.
- **Fix:** a `PLAIN LANGUAGE` block appended to `buildDiarySystemPrompt()`, placed LAST (after `stageVoice`) so recency keeps it winning over stage 0's *"analytical distance"*. It bans describing herself or Zani in technical/biological terms and gives plain substitutions.
- **Generation side — suggestive, not proven.** Before/after at n=30 each: banned terms **5/30 (17%) → 1/30 (3%)**, Fisher one-sided **p = 0.097**. A 5x reduction in the right direction but short of p<0.05. Shipped on the combination of a proven consumption mechanism, an asymmetric payoff (no measured cost), and no detected regression.
- **bugs.md 65 verified intact:** angle rotation and the avoid-list are untouched, and opener variety **improved** (15/30 → 19/30 unique). An earlier 8→6 reading was small-sample noise.
- **Scope limit — only future entries.** Existing clinical entries stay in the 7-entry window until they age out, and in the `amadeus_diary` Chroma collection indefinitely (improvements-backlog #161). Generator + corpus is the complete remedy.
- **Known gap:** `main.js`'s hardcoded fallback diary prompt (bugs.md 57) still carries the OLD wording. It only fires if the renderer omits `diarySystemPrompt`, which it never does — but it should be updated on the next `main.js` rebuild (bundle with backlog #165).
- **Verified:** 31/31 structural assertions on the shipped function across all 5 relationship stages plus an out-of-range stage — returns a non-empty string, rule present and LAST, `Entry —` prefix intact, bug-65 machinery intact, no throw.
- **Live-verified (Aug 23, 2026):** Zani pressed Reset and confirmed the new entry "looks like a person more than before." A single entry is not statistical proof — the generation-side figure remains 17% → 3% at p=0.097 — but it is the real-world outcome the fix targets.
- **File:** `amadeus.html` (`buildDiarySystemPrompt`)


### 70. The long-term memory summary was stored truncated mid-sentence, in every prompt
- **Bug:** the stage-2 diary rollup (`main.js`, Step 4 of `runDiaryOnClose`) generated with `num_predict: 100` while its own system prompt asked for **"3-4 sentences"** of dense prose, and stored the result with `sresult.message?.content?.trim()` — **no completeness check of any kind**. The fragment went into `amadeus_diary_summary` and was injected by `formatLongTermImpressions()` into **every prompt** as LONG-TERM IMPRESSIONS until the next diary write. Found in Zani's `dumpLastTurn()` capture: his live system message ended that block with *"Ultimately, the entries suggest that despite"*.
- **Blast radius is what makes this different from bugs.md 67.** A truncated *reply* costs one turn. A truncated *summary* sits in the prompt on every turn, for as long as it takes to be regenerated — and it is presented to her as settled knowledge about Zani.
- **Measured before building, n=30 per arm, against live Ollama 0.32.15** with a realistic 12-entry input: `num_predict: 100` truncated **19/30 = 63%**; `num_predict: 180` truncated **0/30**. Fisher exact one-sided **p = 2.7e-08**. This was never a rare event — roughly two of every three summaries were fragments.
- **Worst-case input measured too**, because the first run only used 12 entries: the diary caps at 50 (`amadeus.html`) and the window is 7, so the true maximum is **43 older entries** = 1,755 prompt tokens. At 180: **0/30** truncated, output 103 median / **132 max**, so 180 leaves ~27% headroom. Wall time 2.91s median, **3.70s max warm** against a 12s `SUMMARY_FETCH_TIMEOUT_MS`. `num_predict: 220` was measured and buys nothing (max 121).
- **Cold-load is not a risk on this path:** one run hit 10.37s, which was the model load (`load_duration` 0.00s on every warm run). The summary call only runs after a *successful* diary call, which returns early otherwise — so gemma4 is always warm by then. 10.37s is inside the 12s budget regardless.
- **Fix, two layers.** (1) `num_predict: 100` → `180`. (2) A new `trimSummaryToLastSentence()` guard applied before the text ever leaves main.js.
- **The guard is deliberately NOT a reuse of `trimToLastSentence()`** (`amadeus.html`, bugs.md 67). That one *keeps* the fragment when trimming would cost more than ~60% of the text, because a chat reply **has already been spoken aloud** — losing most of what she said is worse than a rough ending. Nothing here is spoken. A summary fragment costs every prompt until the next close, so the trade-off inverts: trim willingly, and return **`null`** rather than store something unusable. Different rule, different name — this is not a duplicated function and there is nothing to keep in sync.
- **`null` is safe by construction:** the caller's existing `if (summaryText)` guards **both** the IPC send **and** the watermark advance, so a refusal keeps the previous good summary and simply retries on the next close. No new control flow was added for it.
- **Not gated on `done_reason`.** Trimming well-formed text is a no-op (the last terminal punctuation *is* the final character), so the guard runs unconditionally. That also catches EOS emitted mid-sentence, and removes any dependence on an Ollama response field — the version already moved 0.21.0 → 0.32.15 under us. `done_reason` is still read, for the log line only.
- **Boundary traps handled:** a naive backward scan cuts at decimals (`"3.5 hours"` → `"He slept 3."`) and at abbreviations — and **"Dr. Pepper" is canon for this character**. Terminal punctuation is only accepted when followed by whitespace or end-of-string, and rejected after a known abbreviation or a single-letter initial.
- **~~Self-healing, no migration.~~ THIS CLAIM WAS WRONG — see bugs.md 72.** It said the summary regenerates whenever `entries.length > watermark`, so every close would replace the bad text. That is only true *below* the 50-entry diary cap. Zani was AT the cap, where `entries.length` is pinned at 50 and `50 > 50` is false forever — so this fix could never fire on his machine, and his live test on 2026-08-26 correctly showed the stored summary byte-identical across a full close/relaunch cycle. Fixed by bugs.md 72 (fingerprint watermark); after that, this entry's fix does reach storage.
- **Verified — unit, 21/21.** `dev/trim_summary_test.js`, run against the function **extracted from the shipped `main.js`** at run time, never a retyped copy: no-op on well-formed text (4 forms), the real captured fragment, mid-word cut, all five refusal paths, decimals, `etc.`, `Dr.`, single-letter initials, ellipsis, and type safety.
- **Verified — integration, against real gemma4 output, n=30 per arm.** Generated real summaries and passed each through the shipped guard. At the OLD `num_predict: 100` the model truncated **22/30**, and **0** truncated summaries reached storage — 30/30 stored results end in terminal punctuation. At 180, 0/30 truncated, 30/30 clean. **Defence in depth is real: even with the old cap, nothing broken would be stored.**
- **Honest limit:** the `null` refusal path never fired in 60 real generations. It is exercised only by the unit tests. The `<40 chars` and `<50% kept` thresholds are therefore reasoned, not empirically tuned.
- **Also fixed in the same commit:** `main.js`'s hardcoded fallback diary prompt (bugs.md 57) still carried the pre-bugs.md-69 wording. The `PLAIN LANGUAGE` clause is now appended, **copied verbatim** from `buildDiarySystemPrompt()`. No behaviour change expected — the renderer always sends `diarySystemPrompt` — so this is a correctness repair, and it closes the known gap recorded in bugs.md 69.
- **Rules checked by number:** 13 (`think:false` intact), 17/18 (close handlers and the `diaryInProgress` force-clear untouched), 19 (hardcoded paths untouched), 28/29/30/38 (boot video untouched — this path runs at close), 33/34/51 (`num_ctx: 8192` unchanged, no KV-buffer resize), 40/67 (this supplies the missing guard on this path), 42/69 (fallback prompt now carries the register rule), 55b (`buildSystemPrompt`/`SYSTEM_PROMPT` untouched — chat KV prefix unaffected), 57 (fallback still present, text only), 64 (no dates written).
- **Gate warning (SINCE FIXED, same day):** at the time of this fix `npm run check` did **not** parse `main.js` — it covered `amadeus.html`, the Python servers and the prompt anchors only, and printed "safe to relaunch" for this change having never read the file that changed. `node --check main.js` was run by hand. That hole was closed hours later by backlog #170; the gate now parses `main.js`, `preload.js` and `preload_call.js`.
- **LIVE-VERIFIED (Aug 26, 2026) ✅** — but only after bugs.md 72 unblocked it. Zani's second attempt: the stored summary ends *"...which is both exhausting and strangely compelling."* A complete sentence. One sample is consistent with the fix, not proof of it; the 63% → 0% figure remains the evidence.
- **File:** `main.js` (`trimSummaryToLastSentence`, the stage-2 summary call, `diarySysContent` fallback), `dev/trim_summary_test.js` (new)

### 71. Her long-term memory was written as a case file, and it is in every prompt
- **Bug:** the stage-2 rollup's system prompt (`main.js`) said *"You are Kurisu Makise's memory system. Summarise these older diary entries ... about Zani"* and — exactly like `buildDiarySystemPrompt()` before bugs.md 69 — **carried no vocabulary constraint at all**. The result is injected into **every** prompt by `formatLongTermImpressions()` as LONG-TERM IMPRESSIONS. So the same feedback loop bugs.md 69 closed on the diary was still wide open on the summary. CLAUDE.md rule 42 already covered it in words (*"Applies to any future memory/summary/fact text too"*); the code did not implement it.
- **Worse than the diary case in two ways.** A diary entry ages out of the 7-entry window; the summary does not — it sits in the prompt until the next diary write regenerates it, and every regeneration used the same unconstrained prompt. And the rate was far higher: the diary measured 17% clinical, this measured **97%**.
- **Measured, n=30 per arm, live gemma4:** therapy/analysis register (`exhibits`, `underlying anxieties`, `validation`, `reliance on`) in **28/30 (93%)** of baseline summaries; **29/30 (97%)** on a fresh confirmation run. With the constraint: **2/30 (7%)** both times. Fisher one-sided **p < 0.00001**, replicated.
- **The bugs.md 69 banned-word list found NOTHING here — 0/30 in every arm.** This is a different failure vocabulary: not lab prose about biology, but case-file prose about a person. The strict list was pre-registered and honestly reported as null; the effect lives entirely in the broader therapy/analysis register measure, which was defined from observed baseline output and then **re-run on fresh samples** to answer the post-hoc objection.
- **Fix:** the `PLAIN LANGUAGE` clause appended to the summary system prompt. The banned-word sentence and the substitutions are **verbatim** from `buildDiarySystemPrompt()`; only the framing sentence is adapted, because a rollup is not "a private journal entry". The shipped string was verified **byte-identical** to the measured arm by extracting it back out of `main.js`.
- **A stronger variant was measured and REJECTED.** Also dropping the *"memory system ... about Zani"* framing in favour of first-person recall scored a perfect **0/30** on register — and **cut remembered content in half**: themes carried fell 4.4 → 2.1, with some summaries carrying **none**. It optimised the metric and destroyed the thing the metric stands for. Do not "improve" this by making it more first-person.
- **Content was measured, not assumed.** Ten themes actually present in the entries, scored per summary. Baseline 3.97 → constrained **4.47**, permutation two-sided **p = 0.186** — no detectable loss, and a high p is the desired outcome for that test. The constrained summaries are also *denser* per character.
- **Cost:** ~135 extra prompt tokens on one call at close. No RAM change, no new component. Truncation stayed 0/30 at `num_predict: 180` (bugs.md 70) with the longer prompt.
- **Rules checked by number:** 13 (`think:false` intact), 17/18 (close handlers untouched), 33/34/51 (`num_ctx: 8192` unchanged), 40/70 (the truncation guard is unaffected and still runs), 42/69 (this is that rule finally implemented on the second generator), 55b (`SYSTEM_PROMPT`/`buildSystemPrompt` untouched — chat KV prefix unaffected), 57 (fallback diary prompt untouched by this change).
- **Live close test: shares bugs.md 70's.** Both write the same artifact and fail distinguishably — 70's failure is a summary that stops mid-sentence, 71's is one that reads like a case file.
- **LIVE-VERIFIED (Aug 26, 2026) ✅** — after bugs.md 72 unblocked it. The regenerated summary is in **first person** (*"I keep finding myself..."*, *"my composure"*, *"my usual detached routine"*), where the frozen one described her in the **third person as "the diarist"**. No case-file vocabulary. It also stayed recognisably her — *"wildly illogical and profoundly inconvenient"* — which is the outcome the rejected first-person variant failed to deliver. One sample; the 97% → 7% figure remains the evidence.
- **Observation, n=2, not actionable:** both the frozen summary and the new one open their final sentence with *"Ultimately,"*. bugs.md 65's opener anti-repetition covers diary entries only, not the rollup. Worth watching, not worth acting on yet.
- **File:** `main.js` (stage-2 summary system prompt)

### 72. The long-term memory froze permanently once the diary hit its 50-entry cap
- **Bug:** the stage-2 summary regenerated only when `entriesData.entries.length > watermark`, and the watermark was stamped as `entries.length` at save time. The diary is **capped at 50** (`amadeus.html`: `unshift` then `if(entries.length>50)entries.pop()`, three sites). So once a user reaches 50 entries the length is **pinned at 50 forever**, `50 > 50` is false, and **LONG-TERM IMPRESSIONS never regenerates again** — it is frozen at whatever text was stored on the close that first reached the cap, and injected into every prompt from then on.
- **Found by the live test of bugs.md 70/71, not by reading code.** Zani ran the before/after check on 2026-08-26: `entries: 50 | watermark: 50` **identical** before and after a full chat → close → relaunch cycle, and the stored summary byte-identical at 602 chars, still ending *"...the entries suggest that despite"*. No `[main:diary-summary]` log lines appeared, because the whole block was skipped.
- **It silently voided two shipped fixes.** bugs.md 70 (truncation guard) and 71 (register constraint) are both correct and both were unreachable on his machine — the generator can be perfect and never run. His frozen summary is simultaneously a 70 failure (ends mid-sentence) and a 71 failure (*"the diarist"*, *"emotional leakage"*, *"façade"*).
- **A wrong claim in this file is corrected by it.** bugs.md 70 stated *"Self-healing, no migration ... corrected on his next close"*. That was reasoned from the code path and was **true only below the cap**. The live test falsified it. The claim is struck through in entry 70 rather than deleted.
- **Fix:** the watermark becomes a **fingerprint of the exact text fed to the summariser** — `crypto.createHash('sha1').update(summaryInput).digest('hex').slice(0,16)` — and regeneration happens when that fingerprint differs from the stored one. `summaryInput` is computed before the gate rather than inside it.
- **Why a fingerprint rather than a bigger counter:** a count cannot see the cap, and cannot see an entry being edited or deleted either — both change what she remembers while leaving the length untouched. The fingerprint is a single source of truth for "has the memory actually changed".
- **Migration is automatic and needs no data touch.** The renderer stops `parseInt`-ing the stored value and passes it through verbatim; main.js compares strings. An existing numeric watermark like `"50"` cannot equal 16 hex chars, so it fails to match exactly once and regenerates. Verified in test: `!/^[0-9a-f]{16}$/.test('50')`.
- **At the cap it now regenerates every close**, because each `unshift`+`pop` moves one entry into the older set and drops another — the summariser input genuinely changes, so the memory genuinely should. Cost is the existing ~3s summary call, already inside the 12s/40s close budget.
- **Verified 13/13** — `dev/watermark_test.js`, gate logic **extracted from the shipped `main.js`** at run time, never retyped: Zani's exact live state (50 entries + numeric watermark 50) now regenerates; idempotent on unchanged input; a new entry at the cap regenerates; edits confined to the 7-entry window do NOT; an edited OLD entry does (a count cannot see this); null/undefined/empty watermarks; pre-cap growth unchanged; fingerprint shape; and no numeric/fingerprint collision.
- **Rules checked by number:** 13, 17/18 (close handlers untouched), 33/34/51 (`num_ctx` unchanged), 40/70 (the truncation guard still runs, now reachable), 42/69/71 (register constraint unchanged, now reachable), 55b (`SYSTEM_PROMPT` untouched — chat KV prefix unaffected), 57.
- **Lesson:** the reasoned claim ("self-healing") survived a code review, a written plan, and a commit message. One live test killed it in a single reading. **A code-path argument about long-lived state is a hypothesis, not a verification.**
- **LIVE-VERIFIED (Aug 26, 2026) ✅ — and this one is a binary state change, not a sample.** Zani's stored watermark went from `50` to `c8e364f1b6441457`, and the summary text changed completely. The gate that had been shut since he reached 50 entries is open. That verification does not depend on sampling: either the fingerprint replaced the count or it did not.
- **File:** `main.js` (summary gate, `crypto`), `amadeus.html` (watermark passthrough), `dev/watermark_test.js` (new)

### 73. The fact extractor silently discarded every fact it found, 33% of the time
- **Bug:** `extractFactsNow()` (`amadeus.html`) ran at `num_predict: 300` in JSON mode. On a fact-dense conversation with the store near `FACTS_MAX` (60), the response hit the cap — and because the output is JSON, a truncation is not a shortened result, it is an **unparseable** one. `JSON.parse` throws, the `catch` logs `[Facts] extraction failed`, and **every fact from that cycle is discarded**. Facts feed `_factsActive`, which is injected into every prompt, so this is silent memory loss precisely when there was most to remember.
- **Found by measuring, not by a symptom.** improvements-backlog #159 asked whether the unguarded `stream:false` paths truncate in practice. The three PROSE paths were measured first and are fine (below). The JSON paths were checked next because they fail differently — and this one was failing.
- **Measured, n=30 per arm, worst case = 60 known facts + a fact-dense conversation:**

  | `num_predict` | truncated | facts lost |
  |---|---|---|
  | **300 (was)** | **10/30 — 33%** | **10/30** |
  | 400 | 1/30 — 3% | 1/30 |
  | **500 (now)** | **0/30** | **0/30**, 431-token max |

- **A typical conversation was never at risk:** 66 tokens median, 96 max, 0/30 truncated at the old cap. The defect is confined to dense windows. A cap costs nothing until it is reached, so raising it does not slow the common case.
- **Fix:** `num_predict: 300` → `500`. `amadeus.html` only — **no rebuild**.
- **Fail-closed was already correct, and that is why it went unnoticed.** All three JSON callers (`extractFactsNow`, `parseDMailRequest`, `studyTick`'s classifier) parse inside `try` and validate fields before use, so a truncation could never corrupt memory — only lose it. Correct design, invisible failure. Worth remembering that fail-closed and silent are the same thing without telemetry.
- **The generalisable rule, and the reason this was predictable:** truncation risk is the ratio between what the prompt ASKS FOR and the cap, not the cap's absolute size. The stage-2 summary asked for "3-4 sentences" against 100 (~0.8x headroom) → 63% truncation (bugs.md 70). This asked for an unbounded list against 300 (~0.8x) → 33%. The three prose paths ask for "one short line" against 80-120 (~4x) → 0%. **Size `num_predict` against the ask, and state the headroom ratio.** (CLAUDE.md 40)
- **Also measured and deliberately NOT changed** — improvements-backlog #159's three prose paths, n=30 each with the real `SYSTEM_PROMPT`, real history and real directives: `fireProactive` (cap 80, 19 tokens median, 27 max), `studyTick`'s remark (cap 80, 18/24) and `checkDMails` (cap 120, 20/36). **0/90 truncated, 0/90 ended mid-sentence.** Adding the bug-67 guard there would be code with no defect to fix. #159 is closed as measured-not-warranted rather than done.
- **Not tested live** — this path runs every `FACTS_EXTRACT_EVERY` (6) exchanges in the background. Raising a cap cannot break parsing that already succeeds, and the common case is unchanged at 66 tokens, so the risk is low; but it has not been observed in the app.
- **File:** `amadeus.html` (`extractFactsNow`)

### 74. The fact extractor held the GPU for ~9s and could not be interrupted (CLAUDE.md 37b)
- **Bug:** `extractFactsNow()` is a background gemma4 caller. CLAUDE.md rule 37 requires every one of them to be **(a) idle-gated AND (b) abortable via `noteActivity()`**. It had (a) — `_factsIdleOk()` — and **not (b)**: no `AbortController`, no entry in `noteActivity()`. `noteActivity()` aborted exactly two callers, `proactiveAbort` and `_warmAbort`. So once an extraction started it ran to completion no matter what Zani did, saturating the GPU that renders Kurisu's Live2D and evicting the chat KV prefix while he waited for a reply. The code comment even asserted the design: *"the idle gate alone decides when it actually runs, which is what protects the GPU."* A gate is not a brake.
- **Found by self-review, and it is partly self-inflicted.** The gap pre-dated this session, but bugs.md 73 raised this call's `num_predict` from 300 to 500 — which **lengthened the un-interruptible window**. Measured worst case (fact-dense conversation, n=10, wall clock): median **6.68s → 8.52s**, max **8.48s → 9.66s**. A correctness fix quietly degraded a responsiveness property, because the cap change was reviewed against the truncation rule (CLAUDE.md 40) and not against rule 37.
- **Fix:** an `AbortController` on the extraction fetch, cleared in `finally`, and aborted from `noteActivity()` alongside the other two — the same pattern `_warmAbort` already uses.
- **Aborting must not cost facts.** The `AbortError` branch sets `_factsDue=true` and re-arms `scheduleFactsExtraction()` (idempotent), so a yielded extraction is retried in the next lull instead of dropped. Without that, this fix would re-introduce the silent fact loss bugs.md 73 had just removed — self-inflicted from the opposite direction. It logs `[Facts] yielded to activity — re-queued`, distinct from the real-failure warning.
- **Verified, live against Ollama 0.32.15:**
  - Structure 7/7 read from the shipped `amadeus.html` — controller created, signal passed, `AbortError` branch, re-queue, `finally` clears, `noteActivity()` aborts, declaration present.
  - **Client releases:** an unaborted heavy call ran **14.14s**; the same call aborted at 1s released in **1.01s** with `AbortError`.
  - **The GPU is genuinely freed, not just the client** — a tiny call issued immediately after the abort completed in **69 ms** against a **119 ms** idle baseline, so it was not queued behind a still-running generation. This distinction is the one rule 37 actually cares about; a client that stops waiting while the GPU keeps working would fix nothing.
- **Known remaining gap — NOT fixed here:** `studyTick()` is the other background gemma4 caller named in rule 37 and it has no `AbortController` either. Untouched this session, so it is logged rather than changed. → improvements-backlog #173.
- **Rule:** "idle-gated" and "abortable" are two different properties and rule 37 requires both. A gate decides when work *starts*; only a brake can end it. Any change that makes a background call LONGER must be re-checked against rule 37, not only against rule 40.
- **Pre-launch review caught two more things in this same fix**, before Zani ran it:
  1. **`let` has a temporal dead zone.** `_factsAbort` was first declared with the rest of the facts state, ~1,150 lines BELOW `noteActivity()`, its only other consumer. Not a live fault — every current `noteActivity()` caller sits inside a function, so nothing reads it during script evaluation — but a future top-level call would throw a `ReferenceError` pointing nowhere near the cause. `_warmAbort` and `proactiveAbort` are both declared above `noteActivity` already; the declaration was moved to match, with a pointer comment left where a reader expects it.
  2. A trailing `// num_ctx MUST stay 8192 (bug 33 family)` ended up annotating the new `signal:` line instead of the `options:` line it describes. Bug 33 is a rule people grep for; a comment on the wrong line is worse than none.
- **Verified 15/15** — `dev/facts_abort_test.js`, with `extractFactsNow`, `noteActivity` and the scheduler **extracted from the shipped `amadeus.html`** and driven against a stubbed fetch: happy path merges and resets state; abort re-queues, clears both flags, merges nothing partial, and logs the yield message and NOT the failure warning; a real (non-abort) failure still warns and does NOT re-queue; and `noteActivity()` called 50x with nothing in flight never throws.
- **File:** `amadeus.html` (`extractFactsNow`, `noteActivity`, `_factsAbort`), `dev/facts_abort_test.js` (new)

### 75. bge-m3 unloaded after 5 minutes, so the first message of a session stalled the GPU
- **Bug:** every embedding call in `kurisu_rag_server.py` (`get_embedding`, `get_embeddings_batch`) omitted `keep_alive`, so Ollama applied its **5-minute default**. Every gemma4 call in the app passes `keep_alive:'30m'`; bge-m3 was the only model without it. The server's startup warm-up (*"embed a dummy string to pre-load bge-m3 weights"*) therefore **expired 5 minutes after launch**, and the first RAG query after that reloaded the model — on the same GPU that renders Kurisu's Live2D.
- **Symptom Zani reported:** "right after my first input after launching, there's noticeable lag for around 2 seconds, her 2D model is lagging while moving."
- **Measured:** cold bge-m3 embed **812 ms**, warm **10 ms** — **81x**. It lands before a single token streams, so the screen shows nothing while the animation stutters. It recurs after any 5-minute lull, not just at launch.
- **Confirmed by TTL, not inferred:** `/api/ps` `expires_at` read directly — `gemma4:latest` unloads in **30.0 min**, `bge-m3:latest` in **5.0 min**. After the fix bge-m3 reads 30.0 min.
- **Fix:** `EMBED_KEEP_ALIVE = '30m'` passed on both embed calls, matching the chat path so both models age out on the same clock. `kurisu_rag_server.py` — **no rebuild**; main.js respawns the server on relaunch.
- **Cost:** bge-m3 stays resident 0.63 GiB for 30 minutes instead of 5. Against the budget measured the same day (gemma4 **4.10 GiB RSS**, 16 GB machine — bugs.md/backlog #172) that is comfortable, and during active use it was resident anyway. **gemma4 is NOT evicted by bge-m3:** measured a gemma4 call at 64 ms immediately after an embed, and `/api/ps` shows both resident (3.02 + 0.63 GiB).
- **A second, smaller contributor was measured and deliberately NOT bundled.** The greeting's TTS translation runs through gemma4 (`TRANSLATOR='gemma4'`), which evicts the chat KV prefix that `prewarmOllama()` had just built: first-message prefill **138 ms → 287 ms** (n=30 per arm, real `SYSTEM_PROMPT`). Real, but **5x smaller than the 812 ms**, and fixing it means touching boot timing (rules 34/36/62/63) where three separate regressions already live. → improvements-backlog #174.
- **Why this hid for so long:** it needs a >5-minute gap between the RAG server starting and the first message — which is the *normal* pattern for launching, watching the boot video, and settling in, but never happens while actively developing and testing in quick succession.
- **Rule:** any model the app depends on interactively must state its own `keep_alive`. A default TTL that is shorter than the user's natural think-time turns a warm-up into a wasted one.
- **POSTSCRIPT 2026-08-31 — the default moved; the fix did not become wrong.** Ollama upgraded
  itself to **0.33.2**, where the default `keep_alive` is **30 minutes, not 5**. Measured directly,
  with the app closed: an `/api/embed` call sent with NO `keep_alive` came back with `expires_at`
  30.0 min out — identical to a call that passes `'30m'`. So on this version the fix is redundant,
  and it becomes load-bearing again the moment the default moves back. **Nothing above is
  retracted:** the 5-minute default and the 812 ms cold load were measured on 0.32.15 and were
  real then. The lesson is not "we did not need it" — it is that a default which silently changed
  twice in one week must never be depended on (CLAUDE.md 44, now restated in those terms).
  **Live-test caveat:** if the first-message stall is gone, this version change is an alternative
  explanation for it. Confirm the fix by reading `/api/ps` `expires_at` while the app runs, not by
  the absence of the symptom.
- **File:** `kurisu_rag_server.py` (`EMBED_KEEP_ALIVE`, `get_embedding`, `get_embeddings_batch`)

### 76. "Don't get the wrong idea" in 37% of tsundere replies — the prompt was teaching it
- **Bug:** Zani reported she "always" says *"Don't get the wrong idea"* when deflecting. Measured with tsundere-triggering probes (affection / praise / concern), n=30: **11/30 = 37%**.
- **It is not the character.** The phrase appears **once** in the 2,522-document RAG corpus — and that one hit is **her own diary entry** echoing it, not VN canon. The 1,672 lines of real Kurisu dialogue never say it. The phrase came from OUR prompt, which quoted it **twice**: once in the INPUT→EMOTION rule as an example of tsundere output, and again in the anti-crutch rule as a phrase to avoid. Naming a phrase in a negative instruction still supplies it as an exemplar.
- **The anti-crutch rule was also too weak by design:** it forbade only *"the same deflection twice in a row"*, so using it every second turn was fully compliant — which is exactly what "repetitive but not consecutive" feels like in use.
- **Measured, n=30 per arm, real `SYSTEM_PROMPT` + real history:**

  | arm | "wrong idea" | p vs baseline |
  |---|---|---|
  | A baseline | **11/30 — 37%** | — |
  | B fix the INPUT→EMOTION line only | 12/30 — 40% | 0.70 |
  | D fix the anti-crutch line only | 10/30 — 33% | 0.50 |
  | **C both** | **3/30**, then **1/30** on fresh samples | **0.0012** |

- **Neither half works alone, and that is the finding.** Each line quotes the phrase, so fixing one leaves the other still naming it and the rate is unchanged. **The phrase has to be absent from the ENTIRE prompt — one mention anywhere holds it at ~35%.** An A/B that changed only one site would have concluded "no effect" and shipped nothing; the interaction is the result.
- **Character was measured, not assumed.** In every arm including the fix: **still deflects 30/30, tsundere/flustered tag 30/30.** She has not gone soft — she deflects just as often, using different words. Distinct openers 17/30 → **20/30**. This mattered: the goal was to remove a catchphrase, not her deflection reflex, and a variant that reduced deflection would have been rejected the way the bugs.md 71 first-person variant was.
- **Fix:** (1) the INPUT→EMOTION rule now describes the *behaviour* (`denies caring, downplays your own concern, brushes something off, or covers embarrassment`) instead of listing phrases; (2) the anti-crutch rule is now **session-scoped** — *"look at what you have ALREADY said earlier in this conversation"* — with six concrete alternative moves and no example phrases. The shipped `SYSTEM_PROMPT` was extracted back out of `amadeus.html` and verified **byte-identical to the measured arm**.
- **Honest limit:** "any stock crutch" (hmph / it's not like / w-what / tch) stays ~90-100% in every arm, including the fix. That is intentional — deflection *is* the character. Only the single dominant catchphrase was targeted, and opener variety improved modestly (17→20 of 30), not dramatically.
- **Rule:** never quote a phrase you don't want her to say — not even to forbid it. Describe the behaviour instead. This is the same class as backlog #163 (an instruction silently overridden by its own examples).
- **`amadeus.html` only — no rebuild.** The system prompt changed, so the first message after relaunch pays a one-time cold prefill; it stays byte-identical within a session, so bug 55b is unaffected.
- **File:** `amadeus.html` (`SYSTEM_PROMPT` — INPUT→EMOTION rule, anti-crutch rule)

### 77. 83% of flirty replies opened "W-what" — the prompt made the stammer mandatory AND named it
- **Bug:** Zani asked for the backlog #177 "Hmph" fix. Measuring it first killed it: on 30 tsundere-triggering probes (affection / praise / concern) **"Hmph" was 0/30**, and 1/30 on daily-life probes — ~1.7% overall. **#177's premise was wrong, and I wrote #177.** It read bugs.md 76's *"hmph / it's not like / w-what stay ~90-100%"* as a rate for "Hmph"; that figure is for the **group**, and the group is carried by a different phrase.
- **The real defect, found by that same measurement:** **25/30 = 83% of flirty replies opened with "W-what"**, with only **3 distinct openers in 30**. That is more than twice the 37% catchphrase bugs.md 76 treated as serious.
- **Cause — worse than bugs.md 76's, because it is compulsory, not merely quoted.** `ROMANTIC/FEELINGS` item 2 read *`Begin with a stammer: "W-what—", "I-I wasn't—", "Th-that's not—".`* — a **mandate plus a three-item list**, and she takes the first item. A sweep found **13 sites** that supplied a stammer token or mandated one; **"W-what" alone was supplied at 4**. bugs.md 76 needed both of its two sites fixed to move at all.
- **The target was derived from the corpus, not invented.** Canon stammers on **48/1672 = 3%** of lines, and **0/64** of the lines the *shipped* retriever returns for those same 30 affection probes. Of the 48 canon lines that do stammer, **42 open differently** — she almost never repeats a stammer. Ours: 100% mandated, one form in 83%. Wrong on **rate** and on **variety**.
- **Fix — replace the LIST with a RULE for forming one.** A list has three members and she picks the first; a rule ("build the stammer out of the word you were ALREADY going to say — repeat its first sound") generates a different stammer per sentence and **supplies no phrase at all, so CLAUDE.md 43 cannot be violated by construction**. Plus: mandate → *"not every reply needs one"*, and a session-scoped *"never reuse a stammer you have already used in this conversation"* — the construction that worked in bugs.md 76. All **12 shipped sites in one pass**; `w-what`/`hmph`/`mandatory` now appear **0 times** in `SYSTEM_PROMPT`.
- **Measured, n=30 per arm, real `SYSTEM_PROMPT` + live RAG, tsundere probes:**

  | metric | baseline | fix | p |
  |---|---|---|---|
  | opens **"W-what"** | **25/30 — 83%** | **11/30 — 37%** | **0.00048** |
  | "what"-family opener incl. respellings | 87% | 50% | 0.0048 |
  | "I-I wasn't implying" | 20% | **0%** | 0.024 |
  | distinct openers | 3/30 | 7/30 | — |
  | flustered/tsundere tag **[GUARD]** | 30/30 | **30/30** | 1 |
  | deflects **[GUARD]** | 27/30 | **29/30** | 0.61 |

- **Character held.** Tag 100% in both arms, deflection unchanged-to-better. The two canon-attested stammers introduced as exemplars (`D-don't`, `N-no`) did **not** become crutches: 1/30 and 0/30.
- **HONEST LIMITS — this is a real win, not a cure.**
  - The "what"-family still opens **50%** of replies (canon: 1 line in 1,672). Distinct openers **7/30** vs canon's 34-in-64. The dominant crutch was halved, not removed.
  - **A new crutch appeared and it is self-inflicted:** `"Don't"` as an opener went **13% → 33%**, because two of my replacement exemplars both start with "Don't" — the exact mistake the old prompt made with "W-what", committed one iteration later. Canon opens with "don't" 1.9% of the time. **Next A/B should target this.**
  - Stammer rate fell **87% → 40%** (p=0.00037). That was **intended** — canon is 3% — but it was declared a quality guard before the run, so it is recorded as a guard that moved. 40% is still 13x canon. Whether it *feels* right is Zani's call, not the metric's.
- **NEGATIVE RESULT — do not re-run.** A second arm added a "vary the MOVE, not just the words" instruction (+241 chars). It bought **nothing**: 'what'-family 50%→60% (p=0.60), stammer 40%→47% (p=0.80), "don't" opener 33%→27% (p=0.78) — all indistinguishable. The smaller arm shipped, on prompt-budget grounds (#156).
- **Verified before shipping:** the `SYSTEM_PROMPT` now in `amadeus.html` was extracted back out and proven **byte-identical to the measured arm** against `git show HEAD:amadeus.html`. `npm run check` 11/11.
- ✅ **LIVE-VERIFIED (Sep 3, 2026, evening).** Zani used her for a full session on the shipped prompt and reported, unprompted: **"she does sound more like Kurisu now."** That is the outcome the fix was for, and it matches the measured direction (83% → 37%). **It is one impression, not a statistic** — and it is recorded next to a defect from the SAME session (see below), because reporting only the good half would misrepresent it.
- **The same session produced a bad reply, and it is NOT a bugs.md 77 regression.** Turn capture (`dumpLastTurn`, `~/Downloads/amadeus_turn.json`, 7 turns) shows *"Now that we've established the parameters of literary archetypes..."* on the casual input *"that's all I need to know"*. Confirmed present in that session's prompt: the bugs.md 77 text (`Build the stammer out of the word` yes, `Begin with a stammer: "W-what—"` no), so the fix was live. Three independent causes are visible in the capture and all pre-date it — see backlog #182/#183/#184.
- **NOT live-verified: the prompt change alters Ollama behaviour**, so this line stood until Zani ran it. Expect a **one-time cold prefill** on the first message after relaunch (the prompt changed); it stays byte-identical within a session, so bug 55b is unaffected.
- **Deliberately NOT changed: 8 hand-written canned strings** still containing "Hmph"/"W-what" (`amadeus.html` 662, 1052, 1081, 1720, 2151, 2156, 2753, 4091 — greetings, Dr Pepper, idle nudge, head-pat, birthday gift). Those are Zani's authored content, not a model bias. **But note the mechanism: `amadeus.html:973` pushes the chosen greeting into `history` as an assistant turn**, so a canned "Hmph" opener sits in the conversation as her own prior words for the whole session. → backlog #179.
- **File:** `amadeus.html` (`SYSTEM_PROMPT`: CHARACTER, CASUAL rule, INPUT→EMOTION, OUTPUT→EMOTION, ROMANTIC/FEELINGS, VARIETY RULE, and 4 exemplars) — **no rebuild, relaunch only.** Mirror reconciled in `docs/kurisu-personality.md`. Harness: `dev/stammer_arm.py`, arms in `dev/canon_arms/`.

### 77b. Self-review of bugs.md 77 — three defects in my own method, found after shipping
Zani asked for a review of the 77 implementation. The fix itself stands; the way I *measured* it had three faults. **Tooling only — `amadeus.html` is unchanged by this entry.**

- **1. I misdiagnosed the timing anomaly from the tail of the log.** I reported that arm B's 1222s wall "was not in the Ollama calls, since per-call times sum to ~60s". **Wrong** — I had only seen the last three lines, which all read ~2s. The stored `.json` says two calls took **933.4s and 242.0s**; per-call wall actually sums to 1220 of the 1222s. The `timeout=120` on the request did not save me. **The real defect is that the summary hid it:** a 20-minute arm looked normal because its tail did. Fixed — `canon_gap_probe.py` now prints median/max per-call wall and lists any outlier. The replies themselves are valid (none truncated), so arm B's *content* stands; only my timing claim was wrong.
- **2. The "deflects" quality guard was circular.** It read 90% → 97% and I reported the character as intact. But **8 of its 16 markers appear in the shipped prompt** — `i'm not`, `that's not`, `not that i`, `whatever`, `as if`, `tch`, `i wasn't`, `stop` — and 5 of those are in the replacement text bugs.md 77 itself introduced. **A guard that scores vocabulary the prompt supplies is measuring the edit, not the character.** The tag guard (100% → 100%) is unaffected and remains the trustworthy one. Added `check_guard_independence()` to `canon_likeness.py`; call it with the prompt before trusting any keyword guard.
- **3. There is NO daily-life regression control.** bugs.md 77 changed the CASUAL rule line (`No analytical words. Stammer, deflect, simple words only.`) and the INPUT→EMOTION line, then measured **only** on tsundere probes. Everyday conversation — where Zani actually spends most turns — was never re-measured after the change. The #176 daily-life baseline was lost with the cleared scratchpad, so this needs **two** fresh arms (~2 min, ~1,700 output tokens, app closed). ~~**Until that runs, "no regression" is an assumption, not a result.**~~ → backlog #181 — **RUN Sep 3, 2026, CLEAN.**
  **#181 result, n=30 per arm, same 30 daily-life probes, BEFORE arm read from `git show 8b0b953~1:amadeus.html` so it is the real shipped prompt, not a hand-revert:**

  | everyday-chat metric | before | after | p |
  |---|---|---|---|
  | length distribution (Wasserstein from canon) | 9.89w | 8.54w | KS **0.24 — no change** |
  | sentences per turn | 3.23 | **3.23** | — |
  | stammer present | 0/30 | **0/30** | 1 |
  | contains a question | 24/30 | 27/30 | 0.47 |
  | tsundere-family tag | 10/30 | 8/30 | 0.78 |
  | distinct openers | 20/30 | 22/30 | — |

  **No regression on any axis.** The stammer change did not leak into everyday chat (0/30 both arms), and the #176 shape defect is unchanged — neither improved nor worsened, which is correct: bugs.md 77 never targeted it.
  **Bonus — this partly restores #176's lost reproducibility.** The BEFORE arm re-creates the daily-life baseline whose raw output was lost with the cleared scratchpad: **W 9.89 here vs 9.15 recorded**, well inside the ~5.0 noise floor at n=30. #176's figures reproduce.
  **One anomaly, pre-existing and NOT caused by this fix:** one `[concerned]` tag (invalid, falls back silently) in the AFTER arm, 0 in BEFORE, p=1. Same tag and same probe as #178 — see that item, now updated with the reproduction.
- **New tool: `dev/prompt_lint.py`.** Pure CPU, <1s, no GPU. Flags (a) phrases the prompt quotes that appear 0 times in canon, split by whether they are quoted to SAY or to FORBID, and (b) exemplar openers over-supplied relative to canon. **It normalises stammer prefixes** — without that, `"D-don't"` and `"don't"` look like different openers and the tool misses the exact mistake it was built for. On the shipped prompt it reports 6 errors, including `"don't"` used by **3/38 exemplars (8%) vs 2.2% of canon** — that is backlog #180, caught mechanically. Also newly surfaced: `you` opens **21%** of exemplars vs 3.9% of canon, `oh` 8% vs 0.8%.
- **Not wired into `npm run check`** — the standing rule is that any new check needs a mutant in `check.selftest.js` in the same commit, and that is a separate piece of work. Run it by hand before prompt edits: `python3 dev/prompt_lint.py`.
- **Files:** `dev/prompt_lint.py` (new), `dev/canon_gap_probe.py`, `dev/canon_likeness.py`. No app change.

### 78. 30% of her memory database was duplicate rows — retrieval was silently weighted by them
- **Bug:** `/index-diary` (`kurisu_rag_server.py`) built each row's id as `date if (date and date not in ids_seen) else f'entry_{i}'`. When several entries share a date — normal; there were four on 31 Aug — the extras got an id from their **position in the array**. Entries are `unshift()`ed onto the front (`amadeus.html:3782`), so **every position shifts by one on each write**, and `upsert` under a shifted id creates a NEW row instead of updating. Each launch re-inserted the same entries under new positional ids.
- **Measured on Zani's live collection: 79 rows for 55 unique entries — 24 redundant copies, 30% of the collection.** One entry stored **5 times**. Mechanism proven, not inferred: those five copies sit under `entry_17, 18, 19, 20, 21` — consecutive positional ids, byte-identical text.
- **Why it matters more than a storage nit:** retrieval returns the nearest matches, so **a memory stored 5 times is 5x more likely to be pulled into her prompt**. Her long-term memory was weighted by which entries happened to collide on a date, not by relevance. This silently amplified exactly the pre-fix clinical entries of backlog #161 — including the ones caught in Zani's Sep 3 turn capture (*"pattern recognition issue"*, *"internal systems"*).
- **Found while investigating something else, and it overturned that investigation.** The starting hypothesis was that the diary GENERATOR was still writing lab prose, and a write-gate was approved to stop it. Deduplicating and splitting at the date bugs.md 69 shipped killed that: **before the fix 13/49 = 27% clinical, after it 0/6.** An earlier "5/10 recent entries are clinical" reading was an artefact of triplicated rows plus a false positive on the word *baseline* used normally. **bugs.md 69 works; the approved write-gate would have fixed nothing.** The duplication was the real defect.
- **Fix, two halves, and they are independent by design:**
  1. **`kurisu_rag_server.py`** — id is now `'d' + sha1(text)[:16]`, so identical text always maps to the same row and duplicates are impossible by construction. **The skip test is on TEXT, not on id**, deliberately: skipping by id would treat every legacy row as absent and insert 50 fresh copies on the first launch after this change — silently doubling the very problem being fixed. Matching on text is correct whether or not the migration has run, so **deployment order does not matter.**
  2. **`dev/dedupe_diary.py`** — one-off migration, dry-run by default, backs up `chroma.sqlite3` and refuses to proceed without a verified backup. Re-keys by add-then-delete so a crash mid-way loses nothing.
- *(2026-09-29, bugs.md 95: the close-time index was removed, so a normal launch now embeds the previous session's entry — usually 1, not 0.)*
- **Bonus fix, same change:** the old code re-embedded **all 50 entries on every launch**, fire-and-forget during boot (`indexDiaryInBackground()`, `amadeus.html:866/977`), on the GPU that renders her — precisely what CLAUDE.md 36/37 and bugs 60/62/63 exist to prevent. With the text skip, **a normal launch embeds 0**.
- **Verified on an isolated COPY of the live database, never on the live one:**
  - migration 79 → 55 rows; **0 texts lost, 0 added**, all 55 dates preserved; re-running is a clean no-op (idempotent).
  - replaying the shipped index logic: **un-migrated db → 0 inserts** (the trap case), **migrated db → 0 inserts**, **migrated db + 1 genuinely new entry → 1 insert.**
- **Deliberately NOT done: deleting entries that exist only in Chroma.** The collection is a superset of the 50-entry `localStorage` diary, and those aged-out entries are real long-term memory. A "mirror localStorage" design would have destroyed them.
- **Limitation:** two entries with byte-identical text collapse to one row, losing the second's date. That is intended — an identical memory twice adds only retrieval weight, which is the bug.
- ✅ **MIGRATION RUN ON LIVE DATA (Sep 3, 2026, 20:14), app closed.** `79 → 55` rows; **0 duplicate texts remain, 55/55 dates preserved, every id content-derived.** The other three collections were untouched and verified after: `kurisu_ja` 756, `kurisu_en` 1672, `amadeus_behavior` 15. Backup at `data/chroma/chroma.sqlite3.bak-20260903-201400`.
- **Clinical exposure moved 29% → 24% of retrievable rows — a real but SMALL gain, and worth stating plainly.** Clinical entries were duplicated more than clean ones (1.77 copies each vs 1.33), so dedupe helped them disproportionately; it still leaves 13 of 55. **Dedupe is correctness, not the cure for #161** — that is backlog #183.
- ✅ **SERVER CHANGE LIVE-VERIFIED (Sep 3, 2026).** Zani relaunched; the collection went 55 → **56 rows, 56 unique, 0 duplicates, every id content-derived.** **One** entry was indexed, not fifty — before this fix that launch would have re-embedded all 50 on the GPU during boot AND re-inserted duplicates under shifted positional ids. Both halves of the fix are now confirmed in production, not just on a copy. `kurisu_rag_server.py` + `amadeus.html` — **no rebuild.**
- **File:** `kurisu_rag_server.py` (`/index-diary`), `dev/dedupe_diary.py` (new). Also reconciled a stale `gemma4 (9.5GB)` comment in `amadeus.html:4778` — that was the disk size, not the 4.10 GiB resident cost (backlog #172).

### 79. `latencyStatus()` reported `rag: null` for every text turn — the stage was recorded, the DELTA was wrong
- **Bug:** on the first live run of the P1 trace (2026-09-06, n=4, all text turns) `latencyStatus()` printed `rag: null` and `stt: null`. `stt: null` is correct — a typed turn has no Whisper stage. **`rag: null` was a defect in the reporting, not missing data.** The raw `latencyDump()` file held `marks.rag` on all four turns: **91, 95, 106, 120 ms**.
- **Cause:** every stage was derived as a delta between two marks — `rag` as `marks.rag - marks.stt`. Marks are offsets from the turn's own t0, and a text turn never sets `stt`, so the subtraction returned null. Only the FIRST stage in the chain has this problem; every later stage has a predecessor that always exists.
- **Why it mattered more than it looked:** RAG was the one stage with no independent cross-check. Prefill is confirmed by `prompt_eval_duration`, and the TTS round trip is confirmed by the server's own `translate_ms + fish_ms`. RAG had neither, so "null" could have been read as "RAG never ran" — and RAG silently falling through is a real failure mode this app already has a circuit breaker for (`_ragDownUntil`). The truth is the opposite: **RAG is the cheapest stage in the pipeline at ~100ms.**
- **Fix:** a separate `dFirst()` helper for the first stage only, which treats an absent predecessor as t0. A voice turn still measures RAG from `stt`; a text turn measures it from the start of the turn. **Confirmed by test that the voice behaviour did not change.**
- **Also added in the same pass:** `prompt_tokens` and `generated_tokens` to the report. Prefill cannot be interpreted without prompt size — prompt tokens climb every turn as history accrues (3884 → 4151 across these four turns), so a rising prefill can look like a regression when it is really a longer conversation.
- **Verified:** the new test was run against the UNFIXED `amadeus.html` with the new test file in place, and it fails there (`✗ text turn reports a RAG stage`); it passes after the fix. 33/33 total. `npm run check` 11/11. `SYSTEM_PROMPT` proven byte-identical to HEAD by sha1.
- **This is the P1 instrument validating itself.** The trace's first live run found a defect in the trace. That is the intended outcome of shipping an instrument before shipping a fix — and it is the argument for reading the RAW dump rather than the summary (bugs.md 77b, defect 1).
- **File:** `amadeus.html` (`window.latencyStatus`), `dev/perf_trace_test.js` (tests 11 and 12). **No rebuild.**

### 80. The tap-to-speak mic path was never instrumented, so real voice turns were logged as "text"
- **Bug:** after a full spoken conversation on 2026-09-07, `latencyStatus('voice')` returned **"no turns recorded yet"**. The conversation had happened; the instrument had not seen it as voice.
- **Two independent causes, and both had to be fixed:**
  1. **There are TWO mic paths and P1 only covered one.** The mic button branches on `voiceFirstOn` (`amadeus.html`, mic-btn handler): Hands-Free **ON** toggles the continuous Silero session (`hfStart`/`hfOnSpeechEnd` — instrumented from the start), Hands-Free **OFF** runs the original tap-to-record path (`startRecording`/`stopRecording` — **not instrumented at all**). A turn on the second path reached `sendMsg`, which called `perfStartIfIdle('text')`, so **spoken turns were silently recorded as typed ones, with no `stt` stage.** That both hid the voice data AND polluted the text medians with turns that were not typed.
  2. **`latencyStatus(kind)` filtered by exact equality.** Even once the manual path recorded, its `'voice-tap'` rows — and the RMS fallback engine's `'voice-rms'` rows — would not have matched `latencyStatus('voice')`. **A filter that hides data reads exactly like data loss**, which is how this presented.
- **Fix:** `perfStart('voice-tap')` at the top of `stopRecording`, `perfMark('stt')` after the Whisper response, and `perfAbort()` on both discard paths (nothing heard, transcription error) per CLAUDE.md 48(b). The kind filter now prefix-matches, so `latencyStatus('voice')` covers `voice`, `voice-rms` and `voice-tap` while `latencyStatus('voice-tap')` still selects just that one.
- **A `voice-tap` total is NOT comparable to a `voice` total, and the code says so.** That path shows a **Send** button and waits for a human to press it, so its total contains unbounded reaction time. Those turns carry `humanSendGap:true`. Read `stt` from them; read the headline number from hands-free turns only.
- **Verified:** the new test was run against the UNFIXED `amadeus.html` and fails there (`✗ voice filter covers voice + voice-rms + voice-tap → got 1`), then passes after. 45/45. `npm run check` 11/11. `SYSTEM_PROMPT` unchanged.
- **The lesson generalises past this bug.** CLAUDE.md 48(b) says enumerate every exit path before shipping a timer. This is its sibling: **enumerate every ENTRY path too.** I traced the hands-free entry and stopped, never asking whether another way into the same feature existed. It did, and it was the default one — Hands-Free is off unless Zani turns it on, so the *uninstrumented* path was the more likely one for him to use.
- **File:** `amadeus.html` (`stopRecording`, `window.latencyStatus`), `dev/perf_trace_test.js` (test 15). **No rebuild.**

### 81. The thinking indicator existed, was styled and animated, and had never once been visible
> ⚠️ **THIS WAS REVERTED THE SAME DAY — READ ENTRY 82 BEFORE ACTING ON ANYTHING BELOW.** The fix
> described here shipped, broke her reply text on every normal turn, and was removed at Zani's
> instruction. The display layer is now frozen (CLAUDE.md 51). Kept as the record of what was
> built and why it failed.
- **Bug:** `sendMsg` switched the typing dots **on** and then **off again seven lines later, in the same synchronous block.** The browser never repaints between two statements, so `.typing.on` was set and cleared within one frame and the indicator has never been seen since it was written. Net effect: from pressing Enter, Zani got `...` in the subtitle and a completely static Kurisu for the whole wait — **4825ms median, measured n=19.**
- **Why it mattered more than a cosmetic nit:** this is the entire feedback channel for the wait. Nothing else on screen acknowledges his message. When the Fish credit ran out on 2026-09-06 he had no way to tell "she is thinking" from "she is broken", and diagnosed a dead API as a bug in the app.
- **Fix:** delete the premature switch-off; hide the dots where her words actually appear instead. **Not in `sendMsg`'s `finally`** — `ttsSpeak` is deliberately not awaited, so `finally` runs at ~2.4s, well before she speaks, and hiding there would have recreated the blank screen. The three display paths (`playSyncedAudio`, `startEstimatedReveal`, `showSub`) cover all six exits: normal reply, sendMsg error, Dr Pepper, D-Mail, TTS failure, TTS timeout. **That coverage was verified against the full audit of the nine subtitle writers, not assumed** — assuming is what caused bugs.md 80.
- **The subtitle now carries only her words**, since the dots carry "thinking". Exception, deliberate: `ollamaStream`'s retry notices (`...Loading model...`) still take the subtitle, because on a cold start that is exactly the message he needs.
- **FAIL-SAFE, and it is the reason this cannot make things worse.** `showThinking()` returns false if the element is missing, and `sendMsg` keeps the old `...` placeholder in that case. The change can never leave the screen emptier than it was.
- **A 90-SECOND WATCHDOG, not 30.** My first plan used 30s. `ollamaStream` retries **10 times with 4s waits — over 40s on a cold model** — and `ttsSpeak` allows 20s on top, so a 30s guard would have blanked the indicator while she was genuinely still working. Sized against the worst case the code permits, per the standing order.
- **A REAL BUG IN MY OWN PLAN, caught by reviewing it before building:** the watchdog was not re-entrancy safe. `sendMsg` re-enables the send button in `finally` at ~2.4s, **before she speaks**, so a second message can start while the first is still synthesising. Turn 1's stale 90s timer would then blank turn 2's indicator — intermittently, and only when typing fast. `showThinking()` now clears any pending watchdog before arming a new one. Same family as CLAUDE.md 48(b).
- **A LIVE-BREAKING BUG I INTRODUCED AND THEN CAUGHT.** Removing the two `...` writes also removed the `const subEn` / `const subEl` declarations at the top of `sendMsg` — but a later line still used both. That is a `ReferenceError` inside the `try` on **every single turn**, which the `catch` would have turned into a popped history entry and an error subtitle. **`npm run check` passed**, because it parses and does not resolve names. Found by auditing the function's identifiers after the edit, not by the gate. → CLAUDE.md **49**.
- **Verified:** `node dev/thinking_indicator_test.js` — 22 checks, driving the shipped block against a fake DOM and a fake clock. **Both critical assertions were mutation-tested:** dropping the watchdog clear fails 3 checks, removing `hideThinking` from `playSyncedAudio` fails 1. `npm run check` 11/11, `perf_trace_test` 45/45, `SYSTEM_PROMPT` proven identical to `pre-p4`, and the revert was exercised in both directions.
- **NOT live-verified — needs a relaunch.** It changes what is on screen during every turn.
- **File:** `amadeus.html` (`showThinking`/`hideThinking`, `sendMsg`, `playSyncedAudio`, `startEstimatedReveal`, `showSub`), `dev/thinking_indicator_test.js` (new). **No rebuild.**

### 82. bugs.md 81 (P4) SHIPPED A REGRESSION AND WAS REVERTED — her reply text stopped appearing
- **What Zani saw, same evening:** *"I cannot view the translated output text now when she reply."* Plus some lag, and — decisively — *"the Amadeus before was great. This change is unnecessary."* **Reverted at his instruction** (`git checkout pre-p4 -- amadeus.html`). `pre-p4` = `dd9fd97`.
- **Root cause, confirmed in the code after the revert:** `playSyncedAudio` **never adds `.on` to `#subtitle`.** It writes text into `#sub-en` and relies on `sendMsg` having made the container visible. `.subtitle` is `display:none` by default; `.on` is what sets `display:block`. bugs.md 81 made that `sendMsg` line conditional on the thinking dots being up — so on **every normal (audio) reply the container stayed hidden and her words never rendered at all.** The no-audio fallback still worked, because `startEstimatedReveal` sets `.on` itself, which is why it was not universally invisible.
- **Why the tests did not catch it, and this is the real lesson.** I audited the **nine writers of `#sub-en`** — who puts TEXT into the element. I never audited who sets `.on` on `#subtitle` — who makes it VISIBLE. **Those are two different responsibilities and I conflated them.** My 22 tests exercised the indicator helpers against a fake DOM and asserted `hideThinking()` was present in the display paths. Not one of them asserted the thing that actually matters: *after a normal reply, is her text on screen?* → CLAUDE.md **50**.
- **`npm run check` was green, the unit tests were green, both mutants were caught, and the feature was still completely broken.** Green gates measured what I thought to measure. This is the same shape as backlog #170 ("a green gate that does not cover your file is not a gate") and bugs.md 80 (I traced one path and assumed it was the only one) — three instances now of the same underlying error: **verifying the mechanism I built instead of the outcome the user needs.**
- **Also reported: lag.** Not diagnosed, because the change was reverted rather than debugged. Candidates if it is ever revisited: the `.t-dot` CSS animation running for the whole wait next to the WebGL canvas, and subtitle container show/hide reflow every turn.
- **The feature itself was unwanted regardless.** Zani: *"When Kurisu is waiting to speak, there's always three dots anyway."* The `...` placeholder already served this purpose. **I solved a problem he did not have** — I inferred it from a latency measurement instead of asking whether the blank wait actually bothered him. Backlog #189 is reopened and should not be rebuilt without him asking for it.
- **Kept from the reverted work:** CLAUDE.md **49** (the deleted-`const` trap) stands on its own and is unrelated to whether P4 ships. `dev/thinking_indicator_test.js` was deleted — it extracts a block that no longer exists.
- **File:** `amadeus.html` restored to `pre-p4`. `npm run check` 11/11 after the revert. **No rebuild.**

### 83. The hands-free session always died 10 minutes after it STARTED, mid-conversation
- **Found:** backlog #195, 2026-09-06. **Fixed:** 2026-09-07, `amadeus.html` only, no rebuild.
- **Bug:** `hf.sessionTimer` was armed once in `hfStart` and cleared only in `hfStop`. **Nothing
  reset it.** So a voice session ended exactly `HF_SESSION_MAX_MS` (10 min) after it began, even
  while Zani was still talking. The constant's own comment said *"auto-end a silent session (#56,
  battery)"* — **silence was never checked.** The comment described the intent; the code measured
  wall time.
- **Fix — the standard idle+absolute timeout pair** (the same structure OWASP specifies for
  session management, and for the same reason: an idle timer alone never ends a forgotten
  session, and an absolute timer alone kills an active one):
  - `HF_IDLE_MAX_MS` (10 min) — **re-armed on every speech onset**, so it now measures silence,
    which is what #56 actually asked for.
  - `HF_SESSION_ABS_MAX_MS` (60 min) — armed once, never reset, so a forgotten session still ends.
    **This half is load-bearing**: a purely resetting timer would have deleted #56's battery
    intent entirely, which is the obvious fix and the wrong one.
- **The trap this could have fallen into:** the reset had to fire for BOTH engines. The mic runs
  Silero when hands-free is on and an RMS fallback otherwise (in practice ALWAYS the RMS fallback —
  Silero has never loaded, backlog #201) — **that split is exactly what caused
  bugs.md 80**, where one path was instrumented and the default one was not. Both route through
  `hfOnSpeechStart`, so the reset hooks that single choke point rather than either engine.
- **Tests:** `node dev/hf_boot_test.js` (17 checks, shared with bug 84). It extracts `hfArmIdle`
  from `amadeus.html` **by anchor** and drives it with a fake clock, so it tests the shipped code,
  not a copy. The outcome assertion is the one that matters (CLAUDE.md 50): *a session with speech
  every 5 minutes survives past the 10-minute cap, and still ends once genuinely silent.*
- ✅ **LIVE-VERIFIED 2026-09-27 on Zani's report:** he talked hands-free for more than 10 minutes and the
  session stayed on. The session is not in the retained Ollama log (it starts 2026-09-25); the fix has been
  in the app since 2026-09-07.

### 84. The boot prewarm kept running THROUGH the boot video — bug 60 reintroduced by a comment
- **Found and fixed:** 2026-09-07. `amadeus.html` only, no rebuild. Flagged but unfixed since Sep 7 morning.
- **Bug:** the boot sequence ran `await Promise.race([prewarmOllama(), delay(4000)])`, and the
  comment above it claimed the prewarm was *"awaited to completion, so it is finished before the
  first frame"*. **`Promise.race` does not cancel the loser.** A prewarm slower than the 4s cap
  kept running — up to its own 30s internal abort — straight through video playback. That is
  precisely the GPU-starvation condition bugs **60** and **63** exist to prevent, reintroduced
  not by a code change but by a comment that stopped being true.
- **Fix:** `prewarmOllama(externalSignal)` now combines the caller's signal with its own timeout
  via `AbortSignal.any` (Chromium 116+; Electron 35 ships Chromium 134), and the boot site aborts
  it once the race resolves. Its internal timer moved into a `finally` — the old code leaked it on
  every failure path.
- **THE HONEST NUMBER, because "aborted" does not mean "stopped" (CLAUDE.md 37 demands this be
  verified, not assumed):** measured 2026-09-07 — an uninterrupted large prefill took **6.58s**;
  abandoned at 0.4s, Ollama stayed busy a further **1.72s**. So the abort bounds the overlap at
  **~1.7s instead of up to 30s. It does not make it zero.** A first probe straight after the
  disconnect waited 1708ms while later ones took 64ms — **a median over 3 samples hid this
  completely**, which is the same mistake that produced the bogus +0.57s KV figure (backlog #196).
- **REJECTED fix, recorded so nobody re-proposes it:** poll Ollama after the abort until it
  answers, so the video provably starts on an idle GPU. That probe is a bare `'hi'` — **exactly
  what CLAUDE.md 34 says evicts the system-prompt KV prefix the prewarm just built.** The fix
  would have destroyed the thing it was protecting.
- **Tests:** `node dev/hf_boot_test.js`. ~~Needs a live relaunch to confirm the boot video still
  plays clean.~~ ✅ **LIVE-VERIFIED 2026-09-27:** Zani relaunched and the boot video played clean
  to the end. The Ollama log shows the renderer prewarm aborted at exactly 4.00s (HTTP 500 at
  12:51:11) — the abort doing its job.

### 85. The voice probe ran with RAG DOWN and reported it as a live-RAG run
- **Found and fixed:** 2026-09-12, backlog #180. `dev/` only — no app code changed.
- **Bug:** `fetch_rag()` in `dev/canon_gap_probe.py` returned `None` on ANY failure, and
  `one_call()` read `None` as "nothing retrieved". The 2026-09-12 opener baseline (commit
  `2061a0e`, `dev/canon_arms/opener_check_20260912.json`) ran after the app — and the RAG server
  it spawns — had closed. The run printed **"RAG: live server on 5003"** and recorded
  **`rag_used` 0/30**. Nobody read that field. The 87% figure was a no-RAG measurement.
- **Second silent shape:** `/retrieve`'s own `except` branch answers **HTTP 200 with every list
  empty**, which the old code could not tell apart from a real "nothing matched".
- **Fix:** `RagDown` is raised for unreachable / non-200 / all-lists-empty. A preflight call runs
  before any gemma4 call, and a mid-run outage stops the run and writes nothing — so one arm can
  never mix RAG-on and RAG-off rows. Checked on 611 real logged retrievals: **0** would have
  tripped the all-empty test falsely. Each row now saves the `rag_block` she actually read.
- **The number it would have hidden:** re-measured with RAG verified up, the crutch is **28/30**,
  not 26/30 (two-sided Fisher p=0.67 — RAG is not the source). The conclusion survived; the
  instrument did not deserve the trust it got.
- **Same class as bugs.md 80 and CLAUDE.md 48(d):** a degraded condition that looks identical to
  the intended one. See CLAUDE.md 52.

### 86. Three #180 measurement tools would have gone blind under a tag-at-the-END prompt
- **Found and fixed:** 2026-09-13, in the plan review, BEFORE any run used them. `dev/` only.
- **Bug:** every tool assumed the emotion tag opens the line.
  1. `prompt_lint.py` found exemplars by `^\[\w+\]`. Under arm G it would find **0 of 38** and
     print "clean" — and `canon_gap_probe`'s lint gate trusts that output.
  2. `opener_family.py` stripped only a LEADING tag, so a G reply's tag counted as a word, every
     reply "ended on ]" (question-ending rate 0), and n-grams contained "flustered".
  3. The blind A/B sheet would have shown the tag's position, revealing which arm wrote a reply.
  Also found: `prompt_lint`'s `STAMMER_PREFIX` missed `Wh-what` (the scorer's twin of backlog #199).
- **Fix:** exemplar = exactly one tag at the start OR the end and no "→" (a naive end-match
  swept in 5 INPUT→EMOTION table lines, 38→43, and would have shifted every lint result; HEAD
  now lints identically: 6 errors, 27 warnings). The probe's lint delta now **fails closed if
  the exemplar count changes**. The scorer reads the first tag anywhere, like `parsEmo`, and
  strips all of them. `blind_ab.py` strips every tag. All covered by `opener_family.py --selftest`.
- **Also fixed in the same review:** the probe's history did not match the app — `"hey"` + a bare
  `[tsundere]` tag, where the app starts with the greeting alone as `[EMOTION:x] text`.


### 87. #180 review 3: the echo detector matched function words, and pairing merged repeated probes
- **Found and fixed:** 2026-09-13, reviewing the Stage 1–2 implementation. `dev/` only.
- **Bugs:**
  1. `is_echo_question` counted ANY shared word except 7, so "My?" echoed "my" and "Thinking about
     me?" matched only on "about"; it also missed word forms (think/thinking). **Corrected
     figures: arm D 18→16, FG 5→6.** The conclusion (every "his words" anchor echoes) held.
  2. It saw only the QUESTION form; "Cute. Right." was invisible. `echo_any` now reports both.
  3. `--compare`, the paired length CI, `opener_stage_table.py` and `blind_ab.py` paired rows by
     probe text. Once n exceeds the 30 distinct probes, the probe list repeats and rows MERGE
     silently. `pair_keys()` adds an occurrence index. No saved run had a repeat, so no result changed.
  4. The lint gate failed on ANY exemplar-count change, which would block an arm that ADDS
     exemplars. Only a drop means blindness; it now fails on a drop.
  5. `--multiturn` had never run. A GPU-free mock test now confirms history growth (1,3,…,15),
     daily/flirty alternation, a fresh greeting per conversation, and G's history transform.
- **Lesson, again:** a detector that gives the right count for the wrong reason is a latent wrong
  count. Read the matches, not just the total.

### 88. The probe's lint gate compared findings by their TEXT, so it misjudged arms that add exemplars
- **Found and fixed:** 2026-09-13, building arm K. `dev/canon_gap_probe.py` only.
- **Bug, both directions:** a finding's message embeds its counts ("8/38 (21%)"). Adding 8
  exemplars turned HEAD's existing `you`/`oh`/`you're` findings into "8/46 (17%)", so the gate
  reported three NEW errors that were not new. The first fix — compare with the numbers masked —
  then hid the opposite case: an arm adding MORE exemplars on an already-flagged opener (oh 3→5)
  passed as "same finding".
- **Fix:** identity = message with digits masked; a finding is new if its identity is new OR its
  "used by K/" count rose. Positive controls, all caught: a worse existing finding, a new
  over-supplied opener, a dropped exemplar. All ten real arms pass.
- **Also in this pass:** `opener_family` put "Wh-Wha...!" outside the what family (it collapses to
  "wha"); fixed, no saved result changed. And the probe printed reply text while running, which
  would have un-blinded a blind rating; `--quiet` added.

### 89. The #180d insult counter scored heat that never happened
- **Found and fixed:** 2026-09-13, reading the first #180d screen's replies. `dev/opener_family.py`.
- **Bug:** `insults_in()` counted the bare words, so "Don't say **stupid** things like that" and "you're
  going to make me sound like an **idiot**" read as her calling Zani a name. The table reported P 2/17
  and PX 3/17 teasing replies with a name. **The true figure was 0/17 for every arm.** It also scored
  F's "running around like an idiot" (a simile) as name-calling in daily chat.
- **Fix:** a name counts only when AIMED at him — after "you" ("you pervert", "y-you big idiot"),
  "you're (such) a/an …", its own exclamation or sentence ("Idiot!", "...Dummy."), a clause tag
  (", dummy."), or "an absolute idiot, that's what you are". 12 selftest cases, including the three
  false positives above and all 6 names in arm X's own examples.
- **Lesson (third time this session — bugs.md 86/87):** read the matches before trusting a count.
- **Extended the same day (180e):** it then MISSED names aimed at him without "you <name>":
  "Don't be an idiot", "You're acting like an idiot". Added; 180d arm P corrected 0/17 → 1/17.

### 90. The #180 Q0 prompt passed every offline guard, shipped, and Zani reverted it on tone
- **Shipped:** 2026-09-19. **Reverted:** 2026-09-22, on his verdict. `amadeus.html` prompt only.
- **What he said:** her tone was *"way too calm"* after lines like *"I just want to chat to you"* and
  *"Do you like me now?"*, and *"I feel like I like her voice before."* Subtitles and expressions were fine.
- **What the offline work had shown:** distinct first words 6→11, widest repeated phrase 9→5, prompt
  copies 11→0, length held, 0 names in daily and sad chat, tags intact. On SINCERE probes it showed MORE
  `[flustered]` (11/13 vs 9/13), so no metric pointed at "calmer".
- **Why the metrics missed it:** every #180 measure counts SHAPE — which word starts a reply, how often a
  phrase repeats, which tag is emitted. None of them measures FELT sharpness. Two changes could plausibly
  flatten her and neither is visible to those measures: the added line *"go soft when he is sincere"*, and
  the removal of her sharper exemplars. The probe also lacks his facts, diary window and memory blocks.
- **Rules that held:** the revert was one command because the ship was one commit, verified byte-identical
  to the tested arm, with `pre-q0-ship` tagged first. Keep doing that.
- **Lesson (CLAUDE.md 53):** for a TONE change, offline metrics can only reject a candidate, never
  approve one. A short live trial with a one-command revert is the real gate — plan for it from the start.

### 91. The greeting audio cache never hit once in ten weeks — the read path lacked `data/`
- **Found and fixed:** 2026-09-27. `amadeus.html` (2 lines) + comments in `main.js` / `preload.js`.
  **No rebuild** — the `main.js`/`preload.js` changes are comments only (verified: no non-comment line differs).
- **Symptom:** Zani: after the boot video, *"it took quite long for Kurisu to generate the greetings"*.
  Reconstructed from the Ollama log and cache timestamps: `...` at ~12:51:24, translate 1.34s, Fish
  ~3.8s, her voice at ~12:51:30 — about **6 seconds** of silence after her reveal.
- **Bug:** since `5ff32ad` (2026-07-13) the writer saved to `AMADEUS_DIR/data/greeting_cache/`
  (`main.js`, `cache-greeting-audio`), but both readers fetched `amadeus-asset://greeting_cache/<key>.mp3`,
  which the protocol handler maps to `AMADEUS_DIR/greeting_cache/` — a folder that does not exist.
  **Every lookup was a miss.** All 88 greetings had a valid cached file (88/88 checked with `afinfo`);
  not one was ever read. So every boot greeting was synthesised AFTER her reveal (bugs.md 63's miss
  path, designed to be rare), and the warmer re-synthesised files that already existed — 4 times on
  2026-09-27 alone, each a gemma4 call next to her animation (CLAUDE.md 37) plus Fish credit.
- **Why it hid for ten weeks:** the miss path is a working fallback — she still speaks, just late.
  It was SEEN once: 2026-08-23, Zani reported `GET amadeus-asset://greeting_cache/… 404`. That session
  checked the file's MODIFIED time, saw "written today", and concluded the cache had been incomplete
  ("expected, self-healing, no action"). **A rewritten file also shows today's modified time.** The
  creation (birth) time would have shown it existed since July; and nobody compared the read path with
  the write path. The 2026-09-06 handoff then claimed cached greetings let her speak on a dead Fish
  balance — never true. The 2026-07-13 claim "cache-hit boots speak instantly" was never exercised.
- **Fix:** both readers now fetch `amadeus-asset://data/greeting_cache/<key>.mp3`. The handler maps
  host+path, so this resolves to the folder the writer uses. The three comments that taught the wrong
  URL (`main.js` ×2, `preload.js`) are corrected — a stale comment caused bugs.md 84.
- **Checked before shipping:** no Fish-server commit since the oldest cached file (2026-07-21) changes
  the audio (`aa2f9c8` adds timings, `eaa2d8c` comments), so `GREETING_TTS_VER` stays `v3`. A hit feeds
  the same `playSyncedAudio(text, audio, emotion)` call as a fresh synthesis; the subtitle reveal and
  its sync are untouched. Zani approved the change against CLAUDE.md 51 on 2026-09-27.
- **Test:** `node dev/greeting_cache_test.js` (5 checks). It tests the OUTCOME: every greeting she can
  pick is READ from the file the writer SAVES, and resolves to an existing file. It reads the shipped
  code by anchor and exits 2 if an anchor moves. **Proven to fail on the old code** (0/88 reachable),
  passes after (88/88). Not wired into `npm run check` (that needs a mutant in `check.selftest.js`).
- ✅ **LIVE-VERIFIED 2026-09-27 13:23.** Zani relaunched and reported it working. The Ollama log agrees:
  boot at 13:23:07, and after her reveal the only call was the diary-index embed (13:23:30) — **no
  translate call, and no cache file written.** A miss does both.
- **Revert:** `git checkout pre-greeting-cache -- amadeus.html` (the behaviour lives only there).
- **Lessons:** (1) a silent fallback hides a 0% hit rate — make a cache report its hits (CLAUDE.md 52);
  (2) to tell "new" from "rewritten", read the file's creation time, not its modified time;
  (3) when a read misses, compare the READ path with the WRITE path before calling it expected.

### 92. The facts store was never written — ten weeks, 0 facts, and nothing said why
- **Found:** 2026-09-27 by the silent-fallback audit (backlog #202). **Fixed:** same day. `amadeus.html`,
  `main.js`, `preload.js` — **rebuilt** (built asar verified byte-identical to the repo). Tag `pre-202`.
  ✅ **LIVE-VERIFIED 2026-09-27 ~17:30 (steps 1–2), Zani's DevTools screenshot.** `factsRuns()`: row 0 `idle`, 746 chars, eval 51, stop, n=2, ok, 1939ms; row 1 `close`, 1304 chars, eval 21, stop, n=1, ok, 1306ms. `factsStatus()`: 3 stored, 3 active. **The idle pass ran AND stored** — so the ten empty weeks were most likely "ran and saw nothing", not "never ran". Step 3 ✅ (same day): with the facts block in her prompt, Zani: *"she sounds the same"*. **Closed.**
- **Symptom:** `amadeus_facts_v1` did not exist in localStorage (log and table decoded), after 21 diary
  sessions since the bugs.md 64 trigger fix. No code path deletes it. Her prompt has never had a facts block.
- **Cause — not proven, both halves addressed:** the idle pass sees only the last 12 lines, and runs only
  after 45s of quiet. Real timing showed long quiet gaps, and the one logged run (09-27 12:53) returned
  `{"facts":[]}`, so "it ran and saw nothing" is at least as likely as "it never ran". A replay of the
  shipped prompt on his real messages found facts in 2 of 13 sessions. Nothing recorded a run, so the
  cause could not be read back.
- **Fix:** (1) a once-per-session **close pass**: main.js Step 5 (LAST, after diary and summary) asks the
  renderer to run `extractFactsNow({close:true})` over the whole session — last 4800 chars, first broken
  line dropped, `num_predict` 800, own 24s timeout, NOT abortable by `noteActivity()` (he cannot type
  under the SAVING overlay). main waits ≤25s, and only if the page sent `factsClose:true`, so a page/build
  mismatch cannot cost a 25s close. (2) `_parseFactsJson`: a cut JSON output keeps every CLOSED fact
  object and drops the unfinished tail (it used to discard all — bugs.md 73); shared by both passes.
  (3) `amadeus_facts_runs_v1` records every run, idle and close (`factsRuns()`).
- **Measured before shipping (backlog #202 table, n=30):** realistic 4800-char chat at 800 → 0/30 cut,
  3/3 facts every run, 3.6s median / 5.4s max (**the close takes that much longer**). A dense 20-fact
  chat cut 1/30 at 800 (the run needed 978 tokens) — salvage keeps its closed facts. 500 cut 30/30.
- **Test:** `node dev/facts_close_test.js` — 29 checks + 3 planted mutants (all caught). Outcome check:
  after a close with a fact in the reply, the fact is IN the store. `facts_abort_test` 15/15,
  `npm run check`, `check:selftest` 7/7, greeting 5, perf 45, hf 17 — all green.
- **First-ever facts block in her prompt:** "THINGS YOU HAVE LEARNED ABOUT ZANI" appears at the next
  boot after the first fact is stored. CLAUDE.md 53: his ear in a live trial is the gate.
- **Revert:** `git checkout pre-202 -- amadeus.html main.js preload.js && npm run build`, **and** in
  DevTools `localStorage.removeItem('amadeus_facts_v1')` — the old code injects stored facts too.
- **Lesson:** a memory WRITER on a user-timed trigger needs a guaranteed run AND a record of each run.
  An empty store looks the same whether the writer failed, never ran, or had nothing to write (CLAUDE.md 52).

### 93. Every Python server wrote into a pipe nothing read — output lost, and a full pipe blocks the server
- **Found:** 2026-09-27 by the silent-fallback audit (backlog #203/#204). **Fixed:** same day. `main.js`
  (rebuilt, asar verified), `kurisu_rag_server.py`, `amadeus.html`. Tag `pre-203`. ✅ **LIVE-VERIFIED 2026-09-29 18:18–18:21** (one session, checked by reading the files): all 6 logs created with spawn headers; whisper output arrives after ~8s of imports; one reply produced a renderer `[Perf]` line, the full fish `[TTS]` chain and rag retrieval lines; 0 LipSync peak/ticker lines kept; at close the Ollama log shows the diary (18:20:51) and summary (18:20:58, 93 tokens) and main.log has no facts-close timeout (1 exchange → skipped-short, as designed).
- **Bug:** `spawnTtsServer`/`spawnHttpServer`/`spawnRagServer`/`spawnWhisperServer` passed no `stdio`, so
  Node gave each child a PIPE, and nothing ever read `proc.stdout`/`proc.stderr`. (1) Every server line was
  lost — errors, watchdog context, the RAG error branch. (2) A pipe that fills BLOCKS the writer: measured
  on a toy child, blocked at ~131 KB. The fish server prints ~860 B per reply → it would hang mid-request
  after ~150 replies in one launch; `ttsSpeak` would time out at 20s and she would go silent, and the
  watchdog would see no exit. Not reached yet (longest launch seen ~30 calls). main.js and renderer
  consoles were not kept either, so 7 audit fallbacks were UNKNOWN by construction.
- **Fix:** `spawnLogged(name, args)`: `stdio: ['ignore', fd, fd]` into `data/logs/<name>.log` (append,
  rotated to `.1` above 2 MB at each spawn, a header line with pid), `PYTHONUNBUFFERED=1`. If the file
  cannot be opened → `'ignore'`, **never** `'pipe'`. `installMainLog()` tees main's console to `main.log`
  (only in the lock-holding instance); `attachRendererLog()` writes the renderer console to
  `renderer.log` — every warning/error, every info line except `[LipSync] peak:` / `[LipSync ticker]`
  (deny-list). Both line logs never throw and cap at 5 MB per session. Also: `/retrieve`'s error branch
  now writes a trace line (#204), `parsEmo` logs an unknown/missing tag (#212, return value unchanged),
  main warns when the fallback diary prompt is used (#210). Disk worst case 24 MB. Logs are local
  (`data/` is git-ignored) and hold her replies and his words.
- **Test:** `node dev/log_sink_test.js` — 29 checks + 4 mutants (33 + 5 since bugs.md 94). CONTROL: the same 2 MB child on an
  unread pipe BLOCKS; OUTCOME: with `spawnLogged` it exits and all 2 MB is in the file.
- **Revert:** `git checkout pre-203 -- main.js kurisu_rag_server.py amadeus.html && npm run build`.
- **Lesson:** a child's stdio is part of its lifecycle. Default `'pipe'` with no reader is a slow-fuse hang
  AND a silent-evidence sink (CLAUDE.md 52). Every spawn must say where its output goes.

### 94. False log lines: an Electron deprecation warning at every launch, and "failures" at every close
- **Found:** 2026-09-29 in the first live logs of bugs.md 93 (backlog #219). **Fixed:** same day. `main.js`
  (rebuilt, asar `main.js` byte-identical to source), `amadeus.html`. Tag `pre-219`. ✅ **LIVE-VERIFIED 2026-09-29 18:44–18:47** (4 text turns, normal close): no deprecation line after the newest `main.log` header; `[unload]` marker then 4 `[BootVideo] … (unload teardown)` lines; no `BGM track not found`; `[Perf]` lines carry `INFO`. No WARNING/ERROR line occurred live, so that level rests on the real-Electron test (check 9).
- **Bug 1:** `main.log` got `'console-message' arguments are deprecated` once per launch. Electron 35.7.5's own
  code (read from the framework binary): `this.listeners("console-message").some(e=>e.length>1)&&warn()` — it
  warns when ANY listener DECLARES more than one parameter, whether or not it reads them. `attachRendererLog`'s
  listener was `(details, lvl, msg)`. **Fix:** `(details)` only. **Probed on the real Electron 35.7.5 (same binary
  as `dist/`, `cmp`):** a 1-parameter listener → no warning; `details.level` is the string `debug` / `info` /
  `warning` / `error`. That mattered: the only live `renderer.log` had 46 INFO and 0 WARNING/ERROR lines, so the
  level mapping had never been seen working.
- **Bug 2:** at close, `beforeunload` clears every media `src`, which fires error events. The BGM `onerror` logged
  `BGM track not found` (false) and then called `tryPlay()` — it STARTED the next track after `audioCtx.close()`.
  The boot-video trail logged `[BootVideo] error`. **Fix:** `_pageUnloading`, set FIRST in `beforeunload`, plus one
  `[unload]` marker line. The BGM `onerror` returns early during unload (no line, no new track). The trail lines are
  KEPT and end in `(unload teardown)` (CLAUDE.md 48d: label, never drop). Safe because Electron fires the window
  `close` event BEFORE `beforeunload`, and main cancels it while the diary runs — so `beforeunload` runs once, at
  the real exit (log: diary 17:20:51Z, unload lines 17:20:59Z).
- **Test:** `node dev/log_sink_test.js` 33 + 5 mutants — check 9 runs the LOG SINK block in the REAL Electron and
  asserts no deprecation line and correct levels; the 3-parameter mutant is caught only there. `node
  dev/unload_log_test.js` 6 + 3 mutants — the flag is already true at every `src` clear; during unload a BGM error
  writes nothing and creates no `Audio`; outside unload the old skip still works.
- **Revert:** `git checkout pre-219 -- main.js amadeus.html && npm run build`.
- **Lesson:** a deprecation can hinge on a function's DECLARED arity, not on what it reads — a "backup" parameter
  is enough to trigger it. And a log line written during teardown needs the same scrutiny as any other: it
  looked like a failure, and the handler behind it was still doing work.

### 95. The close-time diary re-index raced the quit — it finished only when a later step kept the app open
- **Found:** 2026-09-29 in the first live `renderer.log` (backlog #218). **Fixed:** same day. `amadeus.html` (no rebuild),
  a comment in `kurisu_rag_server.py`. Tag `pre-218`. ✅ **LIVE-VERIFIED 2026-09-30 (2 launches).** Launch 1 (4 turns, close 19:32): no `diary index skipped`, no `/index-diary` at close, `diary_index_check.py` → 1 missing (the new 19:31 entry), exit 3 — as expected. Launch 2: `rag.log` 19:33:27 `upserted 1 new entries`; check → **0 missing**, 69 documents, exit 0. **In launch 2 the diary was read from `000118.ldb`** (LevelDB had compacted it) — the `.ldb`/Snappy path, added during the build, was needed on the very first real use.
- **Bug:** `onSaveDiarySummary`'s `finally` acked main (`diarySummarySaved()`) and THEN fired `indexDiaryInBackground()`,
  never awaited. Main went on at once, ran Step 5 (facts) and quit; `stopServices()` SIGTERMs the RAG server.
  **Evidence, same day:** a 1-message close (facts skipped) → `[RAG] diary index skipped: Failed to fetch` at the
  unload millisecond; a 4-message close (facts ran 0.84s) → `upserted 1 new entries`. Timing decided it. Harm was
  nil: the next boot's index added the entry (18:45:06 `upserted 1`), and a check on copies found **50/50** diary
  entries in ChromaDB. But it was unawaited work during shutdown, a false failure line, and a window in which the
  quit could kill the server mid-`upsert` (effect untested — backlog #220).
- **Fix:** removed the close-time call. localStorage is the source of truth, ChromaDB a derived index, and the boot
  index (both boot paths) is an idempotent reconciliation — `/index-diary` skips by text. Rejected: awaiting it at
  close (new IPC + preload + rebuild, inside a 40s budget that 12+12+25s can already exceed, and a timed-out await
  still leaves the server writing at the kill). Cost: +1 bge-m3 embed per boot (~40ms warm), after the reveal — this
  already happened after every close that lost the race. Her prompt is unchanged: the newest entry is in the 7-entry
  window regardless of RAG.
- **Test:** `node dev/diary_close_index_test.js` — 8 checks + 3 mutants (the shipped handler extracted by anchor:
  summary saved, main acked exactly once on every path, 0 index calls and 0 fetches at close; both boot paths
  still index). **Outcome tool:** `python3 dev/diary_index_check.py` — decodes LevelDB `.log` AND `.ldb` (Snappy,
  pure Python; highest sequence wins) and reports diary entries missing from ChromaDB; exits 1 if it cannot read.
  Negative control: one row removed from a COPY → exactly 1 missing, exit 3.
- **Revert:** `git checkout pre-218 -- amadeus.html kurisu_rag_server.py`, then relaunch.
- **Lesson:** for a derived index, reconcile at startup and CHECK THE INVARIANT; do not fire unawaited writes on the
  way out. A log line said "skipped"; only a check of the data could say whether anything was lost.

### 96. A memory-panel change re-selected her facts UNRANKED — boot ranks them
- **Found:** 2026-09-27 while planning #216 (backlog #217). **Fixed:** 2026-09-30. `amadeus.html` only (no rebuild).
  Tag `pre-217`. ✅ **LIVE-VERIFIED 2026-09-30 19:52:** same 3 facts, same order, before and after a refresh in
  DevTools; no renderer error. The >20 effect rests on the offline test (the store holds 3 facts).
- **Bug:** boot selects the 20 facts she sees with `initFacts()` — ranked by `_factRank` (upcoming event first, then the
  last week, then the rest). After a memory-panel add, edit or delete, `_memoryRefreshActive()` re-selected them with
  `loadFacts().slice(0,FACTS_INJECT_MAX)` — STORE order. Two effects for the rest of that session: (1) above 20 facts, a
  live upcoming event past store position 20 fell out of her prompt; (2) at any size, a dated fact that ranks above a
  fact stored before it lost its place (with only undated facts the order is the same — they all rank 2 and the sort
  is stable). The backlog said only (1). Not reached yet: the store holds 3 facts, and a panel change is rare.
- **Fix:** `_memoryRefreshActive(){ initFacts() }` — ONE selection policy for both read paths. The store order is not
  touched (the panel rows use store indices; ranking the store would make the next edit change the wrong fact). The
  in-session extractor still does NOT refresh the active set (boot freeze, CLAUDE.md 41). Her boot prompt is
  byte-identical; after a panel change it is now the prompt the next boot would build.
- **Test:** `node dev/facts_refresh_rank_test.js` — 7 checks + 3 mutants. Shipped code extracted by anchor; outcomes in
  `formatFactsSection()`: 25 facts with the exam at store position 22 stay in the prompt after add, delete and edit;
  the active set after each change equals a fresh `initFacts()`; an added fact appears at once; boot output is
  byte-identical to `b8e929e` on 4 fixtures. Mutants: the old slice, `initFacts` without its sort, a refresh that
  does not re-read the store.
- **Revert:** `git checkout pre-217 -- amadeus.html`, then relaunch.
- **Lesson:** two code paths that select the same thing must call the same function. A copy of the selection with the
  ranking left out looked like a refresh and was a different policy.

### 97. A Whisper repetition hallucination passed the hands-free gate — loops are CONFIDENT
- **Found:** 2026-09-27 audit (backlog #205): `rag_trace.log` 12:52:02 holds "What a great deal, a great deal, a great
  deal, …" as a hands-free (`voice-rms`) query; Zani confirmed he did not say it, and she replied to it. **Fixed:**
  2026-09-30. `amadeus.html` + `kurisu_whisper_server.py` (no rebuild). Tag `pre-205`.
  ✅ **Live-checked 2026-09-30:** 0 false positives on 11 real utterances (ratios 0.33–1.74); one real junk output
  ("you currently", 74 segments, ratio 10.89) discarded. The loop case CANNOT be produced by speaking: Whisper
  transcribed 8 spoken repeats of "a great deal" as ONE — it de-duplicates real speech, so the "real phrase said 4×"
  limit below is also less likely than first thought. The loop case is verified offline only.
- **Bug:** the gate (`hfHandleUtteranceBlob`) checked only `no_speech_prob > 0.6` and `avg_logprob < -1.0`. A repetition
  loop has sound in it and is decoded with HIGH confidence, so it passes both. Whisper's own third failure signal —
  the compression ratio, `mlx_whisper/decoding.py` — was computed per segment and never sent to the app. The loop also
  ended in "," so the rescue hold (`HF_RESCUE_RE`) kept it 1600ms and then sent it.
- **Fix:** two signals, either one discards (same `hfAfterDiscard('gate')` path; nothing new on screen, rule 51):
  **(A)** the server returns `compression_ratio` = the MAXIMUM over segments; the gate discards above
  `HF_COMPRESSION_MAX = 2.4` (Whisper's default, used per segment as Whisper uses it). **(B)** `hfRepeatRun(text)` — a
  2–6 word group repeated `HF_REPEAT_MIN = 4`+ times in a row — catches a loop Whisper SPLIT into short segments,
  where each segment's ratio is low. The discard line now names the reason (`nospeech|logprob|compression|repeat`) and
  whisper.log prints `compression=` and `segments=` per utterance (rule 52).
- **Measured before building (pure CPU):** the hallucination's first 80 chars → ratio 3.08. **The ratio on a WHOLE
  transcript is length-biased** — natural English (canon windows) median 1.09 at 100 chars, 1.74 at 900, 2.00 at 3000,
  with 1/300 above 2.4 at 900 — so it is NOT applied to the whole transcript (no maximum utterance length exists).
  Rule B at 4+ repeats: **1 hit in 4403 real texts** (1511 trace queries, 1672 canon lines, 1220 of her replies — the
  hit is the hallucination) and 0 in 500 canon 1500-char windows; at 3+ it also hit a canon line ("gah hoh ×3").
  The shipped JS function was re-run on the same corpus: same result.
- **Known limits:** a 3-repeat loop split into short segments still passes; a real phrase said 4× in one breath is
  dropped (he must say it again). There are no real Whisper transcripts of Zani yet — whisper.log now keeps the
  ratio of every utterance. The upstream cause, RMS instead of Silero (#201), is not fixed by this.
- **Test:** `node dev/whisper_gate_test.js` — 12 checks + 3 mutants (shipped gate by anchor, stub fetch; outcome =
  submitted or discarded: one-segment loop, split loop, loop ending in ",", normal, "no no no no", 3-repeat, a
  ~1500-char monologue, old server without the field, ratio exactly 2.4, the old two discards, empty).
  `python3 dev/whisper_server_test.py` — 4 checks (mlx_whisper stubbed before import, Flask test client).
- **Revert:** `git checkout pre-205 -- amadeus.html kurisu_whisper_server.py`, then relaunch.
- **Lesson:** a gate built from a subset of a model's own failure signals has a hole where the missing signal was.
  And a threshold taken from a library is only valid at the scope the library applies it (per segment, not per text).

### 98. The server sent `"speed": 1.1` for months, and Fish never applied it — a dead field and a false log line
- **Found:** 2026-09-30 by #221 Step 0 (backlog #225). **Fixed:** 2026-09-30, `kurisu_fish_server.py`. No rebuild.
- **Bug:** `fish_tts()` put `"speed"` at the TOP level of the request. Fish reads speed only from `prosody.speed`, so
  the field was ignored (0.6 vs 1.8 → 7.73s vs 8.05s; `prosody.speed` 0.6 vs 1.8 → 13.06s vs 4.21s). V3's "fixed 1.1"
  and the older `compute_speed` variance were never heard. `/speak` still logged `[TTS] Speed: 1.1x` on every reply,
  and four docs repeated it — a false statement of what she sounds like.
- **Fix:** option (a) of #225, Zani's choice (*"pace is fine"*): remove the field, the `speed = 1.1` line and the log
  line. **No audio change** — the field was ignored, so `GREETING_TTS_VER` stays `v3` (it became `v4` with #221b, bugs.md 99). `compute_speed()` stays
  (uncalled; `dev/voice_ab_test.py` imports it). The dev helper `dev/voice_221/common.synth` no longer takes `speed`;
  `step0_speed.py` now sends an explicit payload, so it still reproduces its measurement.
- **Test:** `python3 dev/fish_payload_test.py` — 16 checks then (21 since bugs.md 99), no network. Drives the real `/speak` (Flask test client,
  translation and `requests.post` mocked) and checks the exact JSON Fish gets: V3 values, no `speed`, no `prosody`,
  `repetition_penalty` 1.2 (bugs.md 54), no `Speed:` log line. Mutants: top-level speed, `prosody.speed`, penalty 1.1.
  **Fails on the old server (6 failures)**, passes on the new one.
- **Revert:** `git checkout pre-225 -- kurisu_fish_server.py`, then relaunch.
- **Lesson:** a parameter the API does not document is not "set" because the request carried it. Check the API
  reference, and measure the effect once (CLAUDE.md 52: a setting that silently does nothing is a silent fallback).

### 99. Fish `prosody.volume` is an undocumented SWITCH — a "small" volume edit moves her ~10 LU (found while shipping #221b)
- **Found:** 2026-10-01, #221b Steps 0–0c (`dev/voice_221b2/step0*_result.json`). **Shipped:** 2026-10-04 with s2.1-pro.
- **Trap:** Fish documents `prosody.volume` as "dB, 0 = no change". On s2.1 it is not a dial: absent or 0 → the loud normalised
  path (median −13.1 LUFS); −1.0 → −22.5; +3.0 → −18.9; −4.5 / −6.0 / −8.5 → ≈ −25.5 (a floor). `normalize_loudness: false`
  alone changes nothing (−12.8). A request without the field is ~10 LU louder than one with −1.0, and nothing errors.
- **Why it matters:** the lip sync (`AMPLITUDE_GAIN=3`, `SILENCE_THRESHOLD=0.012`) and BGM ducking are tuned to s2-pro's level
  (−22.0 LUFS). s2.1 at its default is ~8.5 LU louder (~2.7x amplitude), which would pin her mouth open.
- **Fix:** `FISH_PROSODY = {"volume": -1.0}` in `kurisu_fish_server.py`, sent as the ONLY prosody field. Peak-to-loudness matched
  s2-pro (12.7 vs 12.15 dB), so the lip-sync input shape matches too.
- **Guards:** `python3 dev/fish_payload_test.py` (21; mutants: no prosody, volume 0, extra prosody fields, model s2-pro — fails on
  `pre-221b`); `python3 dev/voice_221b2/level_check.py MANIFEST` ($0: new greeting files vs the same greetings at v3).
- **My own errors on the way (kept as the record):** Step 0's ±1 st pitch gate was tighter than the estimator (erratum 1); Step 0b
  assumed a slope and had no flat-response check (erratum 2); Step 0c's scorer pooled Step 0b's confirm clips and printed a false
  FAIL (fixed with a mutant, re-scored on the saved clips — `step0c_result_bug_pooled.json`).
- **Rule:** CLAUDE.md 54. Revert of the whole ship: `git checkout pre-221b -- kurisu_fish_server.py amadeus.html dev/warm_greetings.js dev/fish_payload_test.py`.
