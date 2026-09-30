# AMADEUS — Reference Document
# Detailed info for Claude Code to read on-demand (not loaded every session)
# Last updated: August 26, 2026

## CREDENTIALS

> 🔑 **No key material lives in this file (2026-08-16).** The plaintext API keys that used
> to sit in this table have been removed, and this doc is now tracked in git like the rest
> of the vault. **Never paste a key back in here.**
>
> - **Live keys:** `config.json` at the repo root — git-ignored, the ONLY source of truth
>   since backlog #146 (Jul 13, 2026). Shape: `{"fish_api_key": "...", "deepl_api_key": "..."}`,
>   loaded by `kurisu_fish_server.py:21-28`. Read it there; do not copy values out.
> - **ElevenLabs** is the legacy backup path and is NOT in `config.json` — its key is still
>   hardcoded in `kurisu_elevenlabs_server.py`, which is untracked and on disk only.
>   Backlog #121 proposes deleting that server outright.
> - **Rotation (backlog #147) is still OPEN**, deliberately deferred by Zani as of
>   2026-08-16. Verified 2026-08-16: none of the three key strings appears in any tracked
>   file or anywhere in git history (`git log --all -S`), so committing this doc exposes
>   nothing — #147 is about keys that existed in pre-git source and in logs.
>
> Identifiers below (voice IDs, model names, endpoint) are not secrets — `c4d832…` is
> already in the tracked `CLAUDE.md`.

| Service | Key/ID |
|---|---|
| Fish Audio API key | → `config.json` → `fish_api_key` |
| Fish Audio Voice ID (neutral baseline) | `c4d832799bf845ee86638a1bc0cd0d41` |
| Fish Audio Voice ID (old expressive) | `fb03cde57e7740c38a9601459afaae42` |
| Fish Audio Model | `s2-pro` |
| Fish Audio Plan | Plus ($11/month) — renew before resuming voice work |
| DeepL API key | → `config.json` → `deepl_api_key` (the value formerly listed HERE, in this doc, was confirmed stale in the 2026-08-11 audit). **The `config.json` key is VALID:** `/v2/usage` → HTTP 200, 0/500000 chars, 2026-09-27 (backlog #207). |
| DeepL endpoint | `api-free.deepl.com` (header auth: `Authorization: DeepL-Auth-Key ...`) |
| Ollama model | `gemma4:latest` |
| Ollama version | **0.34.4** (measured live `GET /api/version`, 2026-09-27; was 0.34.0 on 2026-09-12 — not benchmarked since). Was 0.21.0, then 0.32.15 on Aug 26, 0.33.2 on Aug 31, 0.33.3 on Sep 4 — **four self-upgrades in seventeen days.** 0.34.0 was benchmarked on arrival and is NOT slower: `dev/translate_probe.py` re-run on the same 30 inputs gave 1023ms vs 1022ms on 0.33.3, prefill 244 vs 243, decode 800 vs 786 (floor ±100ms). Backlog #196's numbers therefore still hold on this version.** Several claims in these docs still rest on 0.21.0 — see improvements-backlog #169. **Do not cite a version from memory; read `/api/version`.** |
| ElevenLabs API key (backup) | → hardcoded in `kurisu_elevenlabs_server.py` (untracked, on disk only; NOT in `config.json`) |
| ElevenLabs Voice ID (backup) | `lWqPzX7f0LZyU6AHcvDv` |

## FILE STRUCTURE

```
~/Documents/Amadeus/
├── CLAUDE.md                 ← Claude Code reads this every session
├── .claudeignore
├── docs/                     ← Obsidian vault — read all files here at session start
│   ├── REFERENCE.md
│   ├── session-log.md
│   ├── bugs.md
│   ├── roadmap.md
│   └── kurisu-personality.md
├── amadeus.html              ← Main UI (NO rebuild needed)
├── main.js                   ← Electron wrapper (requires npm run build)
├── package.json              ← Build config (requires rebuild)
├── preload.js                ← Electron preload — IPC bridge (15 channels; diary-on-close + facts-at-close + call/window/greeting-cache)
├── kurisu_fish_server.py     ← Fish Audio S2 Pro TTS server (ACTIVE)
├── kurisu_elevenlabs_server.py ← Old ElevenLabs server (backup)
├── launch_amadeus.sh         ← Backup launch script
├── amadeus_startup.mp4       ← Boot video
├── live2d/Kurisu/            ← Live2D model (Cubism 4)
├── music/                    ← BGM mp3 files
└── assets/                   ← icon.icns etc
```

## HARDWARE CONSTRAINTS

- **16GB RAM** (verified `hw.memsize`, Apple M5) — cannot run Fish Speech S2 local (~20GB required)
- **num_predict 120** — short responses only (word limits enforced in system prompt)
- **gemma4:latest** (8.0B, Q4_K_M) — improved instruction following vs gemma3
- **gemma4 memory, measured 2026-08-26** — three different numbers get quoted for this model;
  they measure different things and only one is a RAM budget:

  | number | value | what it is |
  |---|---|---|
  | `ollama list` SIZE | **9.6 GB** (8.95 GiB) | the model FILE on disk. **Not a memory figure.** This is the source of the old "~9.6GB" anchor. |
  | `/api/ps` `size_vram` | **3.02 GiB** | Ollama's own accounting — lower than the real process footprint |
  | **`llama-server` RSS** | **4.10 GiB** | **the resident cost — use this one.** Stable at 4.11 GiB after a 1,089-token prompt + 400-token generation. |

  The model is memory-mapped, so the 8.95 GiB file is not resident; file-backed pages sit in
  the evictable page cache. RSS is the honest "must stay in RAM" figure at `num_ctx: 8192`.
- **NOT yet measured: the full Amadeus stack.** The four Python servers (Fish TTS, RAG +
  bge-m3, Whisper) plus Electron were not running when the above was taken. gemma4's 4.1 GiB
  is one line of the budget, not the total. → improvements-backlog #172.

## TTS PIPELINE (kurisu_fish_server.py) — current as of April 23

```
User message → Ollama (gemma4:latest) → English response
→ /speak endpoint on port 5002:
  1. Pre-process names: "Kurisu" → "クリス", "Makise Kurisu" → "牧瀬クリス", etc
  2. Translation EN→JP — **gemma4 is PRIMARY** (`translate_via_gemma()`, register-aware Kurisu prompt, temp 0.3, num_ctx 8192). DeepL is FALLBACK only. Toggle: `TRANSLATOR` at top of kurisu_fish_server.py
  3. Post-process: fix_japanese() repairs mangled names
  4. add_prosody_tags(): inject emotion-conditional breath/pause tags
  5. Prepend emotion tag (voice actor direction) before Japanese text
  6. ~~compute_speed()~~ BYPASSED since V3 (2026-07-13): speed is FIXED at 1.1. Function retained but unused
  7. Fish Audio S2 Pro API call — V3 config: temperature 0.7, top_p 0.8, repetition_penalty 1.2, normalize True, speed 1.1
  8. Return: {"elevenlabs": true, "audio_b64": "...", "char_timings": null, "total_duration": 0,
              "timings": {"translate_ms": int, "fish_ms": int, "translator": "gemma4"|"deepl"}}

`timings` was added Sep 4, 2026 for the P1 presence trace (backlog #186). **Durations only,
in milliseconds — never timestamps.** This process's `time.perf_counter()` and the renderer's
`performance.now()` are different clocks and must never be subtracted from each other. The
renderer treats a missing or malformed `timings` block as "unknown" and records nothing, so an
older server and a newer renderer stay compatible in both directions. `translator` says which
engine paid for the time: gemma4 runs on the SAME GPU that renders her (CLAUDE.md 37), DeepL
is network. The no-audio path (translation unavailable) returns `timings` too, with
`fish_ms: null`.
```

## OLLAMA API PARAMS (amadeus.html)
```javascript
// Main chat call
options: {temperature: 0.85, top_p: 0.9, num_predict: 120, num_ctx: 8192}
think: false  // CRITICAL — disables gemma4 thinking mode, keeps content in message.content
keep_alive: '30m'
```

## FISH AUDIO API PARAMS
Verified against `kurisu_fish_server.py:441-453` on 2026-08-16.
```python
payload = {
    "temperature": 0.7,         # V3 (was 0.8)
    "top_p": 0.8,
    "repetition_penalty": 1.2,  # NEVER 1.1 — triggers the phoneme loop (bugs.md 54)
    "normalize": True,          # V3 (was False)
    "speed": 1.1,               # V3: FIXED (compute_speed retained but bypassed)
    "chunk_length": 200,
    "mp3_bitrate": 128,
    "latency": "normal",
}
```
⚠️ `repetition_penalty` was documented here as `1.1` until 2026-08-16 — the exact
value bugs.md 54 forbids. Source has always been 1.2. If you are about to "restore"
1.1 because a doc says so, don't.

## PROSODY SYSTEM (add_prosody_tags)
- No separate EMOTION_OPENER — Fish Audio vocalises English openers as speech (bug 21)
- Breath sounds emotion-conditional:
  - HIGH_AROUSAL {angry, annoyed, excited, scared, surprised, flustered, embarrassed}: [exhale] after ！
  - MED_AROUSAL {happy, teasing, smug}: [soft exhale] after ！
  - Low arousal (all others): [pause] only — no breath sound
- Sentence pauses: HIGH/MED → [pause], low → [silent pause]
- Comma pauses: HIGH → [short pause], others → [brief pause, no breath]
- Re-anchor tags injected between sentences (len(parts) >= 2) to prevent tone drift
- SIGH_EMOTIONS: {annoyed, dismissive, sad, melancholic}

## SUBTITLE SYNC (amadeus.html)
```javascript
audio.addEventListener('loadedmetadata', () => {
    const audioDurationMs = audio.duration * 1000
    const displayMs = Math.max(audioDurationMs * 0.95, wordCount * 80)
    const msPerWord = wordCount > 0 ? displayMs / wordCount : 280
    audio.play()
    // word reveal timer using msPerWord...
})
// 300ms fallback if loadedmetadata never fires
```

## GEMMA4 SPECIFIC HANDLING
- `think: false` in every Ollama API call — prevents thinking mode
- Think token stripping in ollamaStream before parsEmo:
  - `<|channel>thought...<channel|>` (channel-style)
  - `<|think|>...</|think|>` (pipe-style fallback)
  - `<think>...</think>` (standard fallback)
- finalText guard: `cleanText.trim() || strippedRaw.trim() || streamedRaw.trim()`
- OLLAMA_FLASH_ATTENTION=1 — safe with Ollama ≥0.20.4 (patched in 0.20.4)
- num_ctx: 8192 — needed because system prompt is ~1278 tokens

## SYSTEM PROMPT (current — Variant B with April 30 additions)
- Lean character card, ~1280 tokens before memory injection
- Sections (in order, re-verified 2026-09-19): IDENTITY → USER intro → ABOUT ZANI (durable facts) → memory injection point (`\nCHARACTER\n` anchor) → CHARACTER → WHAT YOU KNOW + RECENT CONVERSATIONS caveat → [RELATIONSHIP directive, before TWO MODES] → TWO MODES (CASUAL word rule + banned list / ACADEMIC) → ENDINGS → EMOTION TAG → INPUT→EMOTION → OUTPUT→EMOTION → ROMANTIC/FEELINGS → RULES → VARIETY RULE → EXAMPLES (38 lines) → time context append → [RAG tail message]
- USER: Zani (ザンニー), he/him pronouns
- ABOUT ZANI section: name, age (18), **birthday (11 June, British format)**, occupation (Student), location (England), interests (rhythm games / 音ゲーム, anime, football, piano, chess) — durable facts only
- RECENT CONVERSATIONS caveat: diary entries are impressions, possibly embellished — treat emotional tone as memory, not specific topics
- CASUAL MODE: ≤35 words, simple everyday words, statement-ending mostly. Casual register applies during emotional moments too.
- ACADEMIC MODE: ≤70 words, science/philosophy/logic only
- Memory injection adds ~350 tokens when populated → ~1630 total. Well under 8192 num_ctx.
- **Time context append (April 30, CORRECTED by bugs.md 64):** `formatTimeContext()` **always** appends today's date and weekday (`CURRENT CONTEXT: Today is ...`) at the end of the prompt — she cannot tell a dated fact has passed without a clock. During 01:00-04:59 a sleep-hours sentence is added **on top of** that. It is NOT an empty string outside those hours; the pre-bug-64 behaviour is what this line used to describe. See `amadeus.html` `formatTimeContext()`.
- Full prompt content in `kurisu-personality.md`

## SESSION MEMORY (Stage 1, April 28, 2026 + April 30 buildSystemPrompt rewrite)

```
amadeus.html:
  formatMemorySection()  reads diary localStorage → up to 7 most-recent entries
  indexDiaryInBackground() runs at BOOT only (both boot paths) — NOT at close (bugs.md 95); /index-diary skips
                         by text, so it reconciles whatever ChromaDB lacks. Invariant: dev/diary_index_check.py
                         strips "Entry —" prefix, defaults missing date
                         returns formatted "RECENT CONVERSATIONS:" block
  formatTimeContext()    (NEW April 30) returns context note for 01:00-04:59,
                         empty string otherwise. try/catch wraps Date access.
  buildSystemPrompt()    (REWRITTEN April 30) handles both injections:
                         - memory injects at \nCHARACTER\n regex anchor (existing)
                         - time context appends at end of prompt (new)
                         empty memory + non-late-night → SYSTEM_PROMPT byte-identical
                         console.warn if memory anchor missing
  sendMsg()              uses buildSystemPrompt() instead of bare SYSTEM_PROMPT
                         (only the chat call — ttsGreeting and generateDiaryEntry use bare SYSTEM_PROMPT)

main.js (diary-on-close):
  runDiaryOnClose()      orchestrator: requests conversation via IPC,
                         runs Ollama from main process (AbortController, OLLAMA_FETCH_TIMEOUT_MS=12s),
                         sends entry back to renderer via IPC for localStorage save
  runDiaryWithExit()     shared exit-with-diary called from BOTH 'close' and 'before-quit'
                         sets diaryHandled=true synchronously (prevents repeat)
                         force-clears diaryInProgress after race (prevents timeout deadlock)
                         calls app.quit() to re-trigger normal quit flow
  Both handlers check (diaryHandled && !diaryInProgress) — only allow close when fully done

Logs (bugs.md 93, 2026-09-27): data/logs/fish.log, http.log, rag.log, whisper.log (child stdout+stderr via
  spawnLogged, rotated >2 MB at spawn), main.log (main console), renderer.log (renderer console minus two
  LipSync debug lines). Line logs cap at 5 MB per session. data/ is git-ignored.
  At close, renderer.log shows `[unload] releasing audio/video …`; boot-video trail lines after it end in
  `(unload teardown)` and are expected, not failures (bugs.md 94). The renderer listener takes ONE parameter.

preload.js (15 IPC channels — verified against preload.js on 2026-09-27):
  Diary (stage 1):
    request-conversation    main → renderer
    conversation-response   renderer → main (sends {conv, model, diarySystemPrompt, factsClose})
    save-diary-entry        main → renderer
    diary-save-complete     renderer → main
    show-saving-overlay     main → renderer
  Diary (stage 2 rollup):
    request-diary-entries   main → renderer
    diary-entries-response  renderer → main (entries array + watermark)
    save-diary-summary      main → renderer
    diary-summary-saved     renderer → main
  Facts at close (bugs.md 92 — Step 5, LAST, only if factsClose===true):
    run-facts-extraction    main → renderer
    facts-extraction-done   renderer → main (sent exactly once on every path)
  Other:
    incoming-call-accepted  main → renderer (already-booted-window path only)
    cache-greeting-audio    renderer → main (persist greeting MP3 to disk cache)
    window-hidden           main → renderer
    window-shown            main → renderer
```

## GREETINGS ARCHITECTURE (April 30, 2026)

```
amadeus.html:
  pickFresh(arr, arrName)  (NEW April 30) freshness wrapper
                           reads localStorage 'amadeus_recent_greetings' (JSON map)
                           excludes recently-picked indices
                           cap: min(floor(arr.length/3), 3)
                           writes updated recent list back
                           defensive: corrupt JSON / fully-blocked pool fall through

  pickGreeting()           routing order:
                           1. read 'amadeus_last_seen' → compute absenceTier (24h/72h/336h)
                              write current time to 'amadeus_last_seen'
                           2. July 25 → GREETINGS_BIRTHDAY (Kurisu)
                           3. June 11 → GREETINGS_ZANI_BIRTHDAY
                           4. June 10 → GREETINGS_ZANI_BIRTHDAY_EVE
                           5. June 12 → GREETINGS_ZANI_BIRTHDAY_AFTER
                           6. absenceTier='long' → GREETINGS_LONG_AWAY
                           7. absenceTier='medium' → GREETINGS_MEDIUM_AWAY
                           8. absenceTier='short' → GREETINGS_SHORT_AWAY
                           9. hour 5-12 → GREETINGS_MORNING
                          10. hour 12-17 → afternoon_pool (mixed)
                          11. hour 17-21 → GREETINGS_EVENING
                          12. hour 1-5 → GREETINGS_SMALL_HOURS (heavier concern)
                          13. hour 21-1 → GREETINGS_NIGHT (late evening)
                           All 11 returns wrapped in pickFresh(arr, arrName).
```

14 greeting arrays in total (2026-08-16 recount against `amadeus.html`): generic `GREETINGS`
plus 13 `GREETINGS_*` arrays — MORNING, AFTERNOON, EVENING, NIGHT, SMALL_HOURS, BIRTHDAY,
ZANI_BIRTHDAY, ZANI_BIRTHDAY_EVE, ZANI_BIRTHDAY_AFTER, SHORT_AWAY, MEDIUM_AWAY, LONG_AWAY,
INCOMING_CALL. (`GREETINGS_INCOMING_CALL` was the one missing from the old count of 13.)
All defensive against corrupt localStorage; never crashes greeting flow.

LocalStorage keys (April 30):
- `amadeus_last_seen` — timestamp ms of last boot. Read on boot, current time written back.
- `amadeus_recent_greetings` — JSON object `{arrayName: [recentIndices]}`. Per-array recency tracking.

Sliding window size: 7 (configurable via `MEMORY_WINDOW_SIZE` constant in amadeus.html).
Diary entry storage cap: 50 (configurable via `entries.length>50` check).
Close-time budget (`main.js:63-66`, verified 2026-08-16): `DIARY_TIMEOUT_MS = 40000` outer race
(covers diary + summary in sequence), `OLLAMA_FETCH_TIMEOUT_MS = 12000` per-call (diary generation),
`SUMMARY_FETCH_TIMEOUT_MS = 12000` per-call (summary generation). Sequential budget: 12s + 12s +
IPC round-trips (≤8s) + headroom (8s) = 40s. `MEMORY_WINDOW_SIZE = 7` here must match amadeus.html.

## MAIN.JS BEHAVIOR
- `webSecurity: false` — required for Electron renderer to fetch local APIs
- Hardcoded paths (Electron doesn't inherit Terminal PATH):
  - `PYTHON = '/opt/homebrew/bin/python3'`
  - `OLLAMA = '/usr/local/bin/ollama'` (added April 28 — `which ollama` if path differs)
- Starts `kurisu_fish_server.py` automatically on launch
- Kills TTS server on app close
- Ollama: only starts if not already running. Spawn wrapped in try/catch + on('error') listener so ENOENT doesn't crash app
- Window opens **immediately** (`createWindow()` is called directly in the ready handler). The old 8-second delay was removed by bugs.md 62 — it was part of the cold-start lag.
- `OLLAMA_FLASH_ATTENTION = '1'` — ⚠️ **safety UNVERIFIED on the current Ollama.** This was confirmed safe on **0.21.0**; the machine now runs **0.34.0** (2026-09-12) — four upgrades past the checked version. The check has not been repeated. Do not simply update the version number here — re-run the check, then restate it with the new version and date (improvements-backlog #169).
- Cache auto-clears: `session.defaultSession.clearCache()` on every launch
- **Diary-on-close coordinator (April 28)** — see SESSION MEMORY section above

## BOOT SEQUENCE (amadeus.html)
- Plays `amadeus_startup.mp4` boot video
- 12 second safety fallback if video fails
- After video: fade out → init Live2D → pick greeting → ttsGreeting()
- `ttsGreeting()` retries up to 8 times (2s between)
- Birthday dialogue (July 25): GREETINGS_BIRTHDAY array + pickGreeting() check

## EXPRESSION DECAY (amadeus.html)
- EMO_DECAY_MS map: short 4s (surprised/scared/angry/excited/flustered),
  medium 7s (happy/tsundere/embarrassed/annoyed/teasing/smug),
  long 12s (sad/melancholic)
- No decay: calm, thinking, lecture, curious, dismissive, sarcastic
- emoDecayTimer resets on each new emotion
- Decay restores currentEmo to 'default', unlocking idle variety

## KEY DESIGN DECISIONS
1. English-only subtitles — no Japanese text display
2. Audio-duration-based subtitle sync — msPerWord from actual audio length
3. Fish Audio cloud > local — S2-pro needs ~20GB RAM
4. Neutral baseline voice + rich emotion tags — better controllability
5. Katakana for Kurisu's name — 紅莉栖 mispronounced by TTS
6. gemma4:latest — improved instruction following vs gemma3:12b, native system role
7. ElevenLabs kept as backup — Fish Audio S2 Pro is primary
8. Streaming Ollama — reduces perceived lag
9. normalize: True — V3 (2026-07-13) chose consistency; the old `False` rationale (dynamic range) lost the A/B listen test
10. Emotion-conditional breath sounds — no audible breathing for calm/neutral speech
11. think:false — prevents gemma4 thinking mode from emptying message.content
12. DeepL key via variable — never hardcode key string in Authorization header
13. **Memory injection at runtime, not in stored prompt** — `buildSystemPrompt()` returns `SYSTEM_PROMPT` unchanged when memory empty. Empty-memory case is byte-identical to original. Zero regression risk.
14. **Diary-on-close runs from main process, not renderer** — renderer's beforeunload kills async work too fast for Ollama generation. Main process has runway via `event.preventDefault()` + `app.quit()` retrigger pattern.
15. **Both close paths share runDiaryWithExit()** — X-button (`mainWindow.on('close')`) and Cmd+Q (`app.on('before-quit')`) route through one function. `diaryHandled` flag prevents double-execution; `diaryInProgress` prevents close-mid-save.
16. **Force-clear `diaryInProgress` after race** — without this, timeout-won race leaves flag stuck true → `app.quit()` deadlock. Critical fix from v3.2 review.
17. **Fragment grammar for Fish Audio emotion tags** — sentence-like clauses ("speaking slowly with weight", "breaking through") get vocalised as English. Noun/adjective fragments stay safe as instruction. Applied to `curious`, `thinking`, `melancholic`, `embarrassed`, `blush`.
18. **Hardcoded `OLLAMA` path** — same pattern as PYTHON. Electron's spawn doesn't inherit Terminal PATH. Defensive try/catch + on('error') so future failures don't crash app.
19. **IME-aware textarea handler** — `e.isComposing||e.keyCode===229` check + `clearMsgInput()` double-clear pattern prevents macOS autocomplete commits from re-inserting cleared text.
20. **Time context appended at END of system prompt, not at memory anchor** — recency bias gives strongest attention. **CORRECTED by bugs.md 64:** the block is no longer conditional — the date and weekday are emitted every hour, because without a clock she asserts stale dated facts as upcoming. Only the sleep-hours sentence is conditional on hour ∈ [1,5). The prompt therefore changes once per day, not once per night; that is intentional and the KV prefix is still stable *within* a day.
21. **Birthdays win over absence** — design choice in `pickGreeting()` routing. Absence detection runs after birthday checks. A user returning after 5 days on June 11 gets the birthday greeting, not the welcome-back greeting. The birthday is the more emotionally specific moment.
22. **Greeting freshness via per-array recency tracking** — `pickFresh()` uses one localStorage key for all arrays as a JSON map. Cap formula `min(floor(arr.length/3), 3)` ensures small arrays never have their pool fully blocked (3-entry array remembers only the last 1 pick).
23. **British date format in ABOUT ZANI** — `Birthday: 11 June` not `June 11`. Kurisu addresses someone in England; British format is more natural. Pure prompt-text choice; code-level date checks remain numeric.

## DEBUGGING GUIDE

| Symptom | Cause | Fix |
|---|---|---|
| Boot video stuck | JS syntax error in amadeus.html | Check for duplicate `const` declarations |
| No voice | Bad audio condition | Check `data.audio_b64` — don't require `char_timings` |
| Wrong Python | Path issue | Check hardcoded `/opt/homebrew/bin/python3` in main.js |
| Ollama fails to start (ENOENT popup) | Electron PATH | Check `OLLAMA = '/usr/local/bin/ollama'` matches `which ollama` |
| Ollama CORS errors | Wrong host | Use `127.0.0.1:11434` not `localhost` |
| Fish Audio 401 | API key / subscription | Check key; renew subscription if expired |
| Emotion tag visible in text | parsEmo() not matching | `validEmotions` Set + regex matching ANY `[word]`. Strips all bracketed tags, only adopts known emotions. |
| Text dumps all at once | Subtitle sync broken | Check wordCount declared before loadedmetadata |
| Audible breathing on calm | [exhale] on wrong emotions | Breath tags only for HIGH_AROUSAL emotions |
| Tone changes mid-response | Re-anchor tags missing | Check EMOTION_ANCHOR and len(parts) >= 2 guard |
| Kurisu silent after input | gemma4 thinking mode | Check think:false in ollamaStream body |
| English spoken before Japanese | Tag has sentence-grammar clauses | Rewrite tag with fragment grammar (see bug 22, 17 in design decisions) |
| DeepL falling back to English | Key hardcoded in header | Use f'DeepL-Auth-Key {DEEPL_API_KEY}' in header |
| Topic invented from "memory" | Diary entries treated as facts | Caveat in WHAT YOU KNOW reminds model entries are impressions; ABOUT ZANI section provides real durable facts |
| Memory section not appearing in prompt | `\nCHARACTER\n` anchor missing | Console will warn. Fix the prompt structure or update regex anchor |
| Diary not saving on close | Several causes | Check IPC handlers wired in preload.js; check the close budget is sufficient for cold-start Ollama (`DIARY_TIMEOUT_MS`=40s outer, `OLLAMA_FETCH_TIMEOUT_MS`=12s, `SUMMARY_FETCH_TIMEOUT_MS`=12s); check renderer is responding |
| Input box won't clear after Enter | macOS autocomplete/IME commit | `clearMsgInput()` already handles via double-clear + `e.isComposing` check |
| App hangs on close | Timeout deadlock | Verify `runDiaryWithExit` force-clears `diaryInProgress=false` BEFORE `app.quit()` |

## PENDING FEATURES

### Tier 2 (next priority)
- ✅ DONE: Stage 1 session memory (April 28, 2026) — sliding window of 7 diary entries, auto-on-close diary writing
- ✅ DONE: Zani birthday dialogue (April 30, 2026) — eve/on-day/after greetings, ABOUT ZANI birthday field
- ✅ DONE: Tiered absence detection (April 30, 2026) — short/medium/long away tiers
- ✅ DONE: Greeting freshness memory (April 30, 2026) — `pickFresh()` helper
- ✅ DONE: Sleep-hours awareness (April 30, 2026) — small-hours greetings + late-night system prompt injection
- ✅ DONE: VN Transcript RAG — Phase 1 May 3, 2026; Phase 2 (diary corpus) May 11, 2026. See `roadmap.md`.
- ✅ DONE: Obsidian MCP integration (May 1, 2026) — `@bitbonsai/mcpvault`. See `roadmap.md`.
- ✅ DONE: Stage 2 session memory (**shipped May 11, 2026** — this line said ⏳ until 2026-08-26). Older-than-window entries are rolled up by Ollama on close into `amadeus_diary_summary` + watermark, injected as LONG-TERM IMPRESSIONS. Its four IPC channels are listed in the SESSION MEMORY section above. Generation is capped at `num_predict: 180` and guarded by `trimSummaryToLastSentence()` (bugs.md 70).
- ✅ DONE: Ollama translation (**shipped July 18, 2026**) — superseded by the gemma4 translator swap (`TRANSLATOR='gemma4'` in `kurisu_fish_server.py`), not a ≤2B model. See roadmap.md.

### Tier 3
- ✅ DONE: Lip sync (May 2-3, 2026) — Web Audio API amplitude + formant analysis; workaround for `char_timings: null`. See `roadmap.md` and bugs.md 31-37.
- Incoming call mode + desktop notifications
- UI identical to S;G 0
- Amadeus internet research
- Fine-tune LLM on VN transcript — RAG (now Tier 2) is the recommended path. **The feasibility numbers in roadmap.md are stale** (costed against gemma3:12b and the old ~9.6GB anchor; the app runs gemma4:8b and the real resident cost is 4.10 GiB). Re-cost before acting — see roadmap.md and bugs.md 76.
- Fine-tune voice on 756-clip dataset (cloud GPU or Fish Audio platform)

## DATASET (756 WAV clips — embedded in the `kurisu_ja` RAG collection since May 3, 2026)
- Location: `~/Documents/Kurisu_Dataset_Pro/` (verified on disk 2026-08-26)
- **EN source corpus: `~/Desktop/kurisu_english_lines.csv`** — 1,672 lines, verified present
  2026-08-26. (An earlier note here claimed `~/Desktop/` did not exist; it does, and it holds
  the file `build_kurisu_index.py:23` reads.)
- **The JA and EN files cover the SAME script, in the same order, at different granularity**
  (verified 2026-08-26). JA `kurisu_0000` 「この携帯、電源切れてる!」 is EN row **5**
  (*"Huh? This phone is off."*); JA row 1 spans EN rows 7-8. The JA clips are **merged
  utterances** (one per WAV), the EN file is **sentence-split**, with roughly a 5-row offset —
  hence 756 vs 1,672. `metadata.csv` is **Japanese**, not English: 755 of its 756 rows contain
  Japanese script, two columns `filename|japanese_transcript`, and it is the only metadata.csv
  in the tree.
  **Why this is worth acting on:** aligned, they yield **756 JA↔EN pairs of her real speech in
  her real register** — precisely what `translate_via_gemma()` in `kurisu_fish_server.py` does
  NOT have today (it translates from a register *description* with no examples). That is a
  concrete, local, free improvement to the VOICE from data already on disk. Alignment is a
  monotonic many-to-one problem (several EN sentences per JA clip), not a lookup — expect a DP
  or embedding-similarity pass, and verify the offset holds across the whole file rather than
  assuming it from the head.
- **Corpus shape matters for any fine-tuning decision.** The CSV schema is `update,line` — bare
  Kurisu utterances with **no speaker context and no preceding dialogue**, i.e. one side of a
  conversation with the prompts stripped. Length distribution: 22% are ≤3 words, 47% are ≤7,
  and only **458 of 1,672 (27%) reach 15+ words**. So there are **zero (input, output) training
  pairs** and roughly 458 substantive style targets. See roadmap.md's fine-tune entry.
- Files: `kurisu_0000.wav` to `kurisu_0755.wav`
- Transcript: `metadata.csv` (pipe-separated: `filename|japanese_transcript`)

## ABANDONED: Fish Speech S2 Local
- Failed: MPS out of memory on 16GB Mac
- Current: Fish Audio cloud API
