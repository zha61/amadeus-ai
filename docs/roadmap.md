# Roadmap — Amadeus Project

---

## ✅ Shipped July–August 2026

*Added 2026-08-16. This section backfills a gap: the roadmap's dated entries stopped at
June 2026 while a full summer of work shipped. **Dates below are the git commit dates**
(`git log --date=short`), cited per item, because `session-log.md` has entries for
July 13 / 18 / 20 and August 11 only — the July 20–21 feature batch (D-Mail, Study Mode,
camera capture, birthday event, memory panel) has NO session-log entry. Nothing here is
inferred; anything the git history did not date is not listed.*

### September 4, 2026 — presence: the direction, and its instrument
Zani set the north star: **Jarvis-style real-time support, with Kurisu's personality, voice and
appearance unchanged.** He chose **presence before awareness**. Presence is a latency problem,
not a feature list, and it is scoped as P1–P5 in improvements-backlog **#186–#190**.
- **✅ P1 — presence latency trace (#186).** One number per turn: *he stops talking → she starts
  talking*, plus the per-stage breakdown. `latencyStatus()` / `latencyDump()` / `latencyReset()`
  in DevTools; `PERF_TRACE=false` disables it without a code revert. `amadeus.html` +
  `kurisu_fish_server.py`, **no rebuild**. Tests: `node dev/perf_trace_test.js` (45).
  **Live-verified on the TEXT path Sep 6 (n=4); the VOICE path on 2026-09-27** (`voice-rms`, `stt 4421`). Its first
  live run found a defect in itself (bugs.md 79) — which is what shipping an instrument is for.
- ❌ **P4 (#189) shipped and was REVERTED on Sep 7** — it broke her reply text, and Zani did not
  want it (bugs.md 81/82).
- 🔒 **The display layer is FROZEN from Sep 7 (CLAUDE.md 51).** P3 (#188) is blocked by it, since
  per-sentence synthesis breaks the audio-duration subtitle sync. P2 (#187) and P5 (#190) are
  deferred — he is a text user, not a voice user.
- ⭐ **What IS still wanted: make her reply faster without losing quality.** Top item is the
  translate step at 1270ms (#196) — a second gemma4 call running after she has finished writing,
  entirely below the display layer.
- **Found while researching this:** Fish Audio has a **WebSocket streaming TTS endpoint**
  (`wss://api.fish.audio/v1/tts/live`). Backlog #153 did not know it existed, and it removes both
  costs #153 called unfixable. See #188.

### August 16–23, 2026 — tooling, KV cache, and her voice
- **Pre-launch gates (backlog #157, extended #170).** `npm run check` parses every inline `<script>` (catching the duplicate-`const` class that used to strand the boot video — CLAUDE.md rule 3), parses `main.js` / `preload.js` / `preload_call.js` (added Aug 26, 2026 — a main-process syntax error is no window and no boot video, and it was the gate's blind spot until then), compiles the four python servers, and asserts the SYSTEM_PROMPT injection anchors exist. `npm run check:selftest` is a mutation test proving the checker still has teeth — 7 mutants including two equivalent ones that must NOT be reported. **Run `npm run check` before every relaunch.**
- **bugs.md 66 — lip-sync node leak.** `createMediaElementSource` nodes accumulated for the whole session; now torn down idempotently. Live-verified.
- **bugs.md 67 — truncation guard.** A reply cut off by `num_predict` used to be spoken AND written into memory. `ollamaStream` now reports `done_reason` and `sendMsg` trims to the last complete sentence. Dev: `truncStatus()`.
- **bugs.md 68 — KV cache.** The per-turn RAG block sat inside the system message, ahead of all history, so the whole conversation re-prefilled every turn. Moved to its own message before the user turn. Measured in isolation 672ms → 176ms; live ~1569ms cold then ~850ms (the remaining gap is the ~431-token RAG block plus gemma4 being shared with the TTS translator — backlog #160). Dev: `perfStatus()`.
- **bugs.md 69 — diary register.** Her diary had no vocabulary constraint, so it was written in lab prose, injected as "in your own past words", and quoted back verbatim (*"your 'biological hardware'"*). A PLAIN LANGUAGE rule now constrains diary generation. Consumption side proven (p=0.027); generation side suggestive (17%→3%, p=0.097).
- **`dumpLastTurn()` (backlog #164).** Captures the exact `messages` array, reply and meta for the last 8 turns so a bad reply can be replayed instead of guessed at. It found bugs.md 69 and backlog #165 within two captures.
- **Docs discipline changed** — CLAUDE.md now requires docs to be updated after EVERY implementation, in the same commit, reconciling reference docs rather than only appending a log entry.

### July 13, 2026 — voice V3, greeting cache, vision
- **Vision — paste an image and she comments on it** (backlog #91, `3c9f1af`). gemma4's image input: paste → downscale ≤1024px JPEG → `images[]` on the Ollama call; history keeps a text marker to protect the KV cache; canon interception skipped when an image is attached.
- **Greeting audio disk cache + prefetch during the boot video** (#32, #79, `5ff32ad`). ⚠️ Never hit until 2026-09-27 — the read path lacked `data/` (bugs.md 91).
- **Voice "V3" config** — temp 0.7, normalize True, "fixed speed 1.1" (**never applied** — Fish ignores the top-level field; the dead field was removed 2026-09-30 and she stays at 1.0, backlog #225) (A/B test `dev/voice_ab_test.py`). See `session-log.md` July 13 entry.

### July 18–19, 2026 — hands-free voice + two core swaps
- **Hands-free voice Phase 2** (backlog #46 #49 #50 #51 #56, `3446f98` + `b5714d4`). Vendored **Silero VAD v5** + ONNX runtime (offline, lazy-loaded) with an RMS fallback; Whisper no-speech/avg-logprob gate; auto re-arm of the mic on her reply `ended`; auto-exit after ~10 min of silence.
- **Translator core swap — register-aware gemma4 replaces DeepL** (`2823e0d`, A/B verdict 7/8). `TRANSLATOR='gemma4'` in `kurisu_fish_server.py`; DeepL is fallback only. **This supersedes the "Ollama Translation (revisit)" Tier 2 item below** — the answer turned out to be the model already resident, not a dedicated ≤2B one.
- **STT core swap — `whisper-large-v3-turbo` replaces medium** (`86a05b1`, verified before swapping).
- **Live2D life batch** — emotion-driven breathing (#58), tsundere look-away (#61), reduced blink rate during speech (#62) (`24c47e5`).
- Also: service watchdog (#80), RAG tuning trace to disk (#3), TTS fetch timeout (#34), scheduler sleep/wake race fixes (#151, #152). See `session-log.md` July 18 entry.

### July 20, 2026 — mind upgrades + D-Mail
- **Structured fact memory** (mem0 pattern, `5956487`). gemma4 (`format:json`, temp 0.2) extracts durable facts about Zani → localStorage `amadeus_facts_v1` (cap 60, dedupe + `replaces` updates). Top 20 injected before the CHARACTER anchor, frozen at boot in BOTH boot paths for KV discipline (a memory-panel change re-runs the same ranked selection — bugs.md 96, 2026-09-30). Dev helper: `factsStatus()`. *(Later corrected by bugs.md 64 — facts gained an `event_date` and the extraction trigger was reachable-in-practice only after that fix.)* **Corrected again by bugs.md 92 (2026-09-27): the store had still NEVER been written. A once-per-session pass at close now reads the whole session (4800 chars, `num_predict` 800), cut output keeps its closed facts, and every run is logged (`factsRuns()`). Live-verified 2026-09-27.** ✅ **Backlog #216 (same day):** undated facts 30+ days old carry a derived
  `[learned over … — it may have changed]` note; a re-stored, replaced or edited fact is renewed and the 60-cap drops the
  least recently renewed. A gemma4 "confirmed" field was measured and REJECTED (`dev/facts_arms/PREREG_216.md`).
- **Hybrid retrieval** (`0c8f1bc`). Okapi BM25 (EN words + JA char-bigrams, zero deps) over both style corpora, fused with dense top-10 by reciprocal-rank fusion. Three iterated fixes: statistical stopwording (>5% df), match-diversity preference, guaranteed lexical slot. Verified: "IBN 5100" probe → 3/3 on-topic.
- **D-Mail — messages through time** (A3, `be60012`). Canon-dressed scheduled reminders; `amadeus_dmails_v1` in localStorage.
- See `session-log.md` July 20 entry (covers the two mind upgrades; D-Mail is undocumented there).

### July 21, 2026 — Study Mode, camera, birthday event, memory panel
*(git-dated only — no session-log entry exists for this batch.)*
- **Study Mode — screen awareness** (B1, `3bacdde`). She watches the screen, fully local.
- **Camera capture** (A1, `3f204b6`). She looks through the camera on demand, one frame at a time — distinct from the July 13 paste-an-image path.
- **Birthday event** (A5, `64b18d9`). Gift moment + day accent + a private diary entry; `amadeus_birthday_v1`.
- **Memory panel** (B2, `9f4c709`). View / edit / delete what she remembers — and she notices when you do.
- Boot-video hardening the same day: bugs.md 59 asset-handler fix (`54ed097`), bugs.md 60 defer prewarm + greeting until after the video (`8ad1ec2`).

### July 25 – August 11, 2026 — performance and behaviour corrections
Recorded in full in `bugs.md`; listed here only so the roadmap is not silent about them.
- **bugs.md 61** (Jul 25, `da5c633`) — background gemma4 work gated + abortable; it shares the GPU with her Live2D rendering.
- **bugs.md 62** (Aug 8, `e19cedf`) — cold-start lag: prewarm vs Live2D collision, late RAG spawn.
- **bugs.md 63** (Aug 11, `29b008c`) — greeting never entered `history` (tonal + content discontinuity) + reveal stutter.
- **bugs.md 64** (Aug 11, `a966a00`) — temporal grounding: she now always knows the date; facts carry an `event_date`.
- **bugs.md 65** (Aug 11, `f98c2b0`) — diary voice collapse (71% of entries opened "Honestly,") broken up.
- ⚠️ **63/64/65 are NOT live-tested by Zani yet** — see the handoff block at the top of `session-log.md`.

---

## ✅ Complete (as of May 3, 2026)

### Added May 3, 2026 (evening)
- **VN Transcript RAG — Phase 1 (dual corpus)** — Two ChromaDB collections: `kurisu_ja` (756 Japanese voice clips via bge-m3) + `kurisu_en` (1672 English LP lines). k=3 per collection, 6 lines injected per turn. English lines framed as style examples; Japanese as tonal anchors. Flask RAG server on port 5003 with health-poll window open. Silent 1.5s fallback — chat always works without RAG. Architecture: `session-log.md` May 3 entry + the RAG section of `CLAUDE.md`.

### Added May 2-3, 2026
- **Lip Sync — amplitude + formant analysis** — Web Audio API drives `ParamMouthOpenY` (jaw drop) from peak time-domain amplitude and `ParamMouthForm` (lip stretch/round) from F1/F2 frequency-band ratio. Pure single-file change to `amadeus.html`. Bugs surfaced and fixed: 31 (Cubism 5 SDK API change), 32 (idle motion override → use `internalModel.on('beforeModelUpdate')`), 33 (`lipSyncValue` doesn't exist in this build), 34 (analyser array sized wrong), 35 (`pow(_, 0.8)` curve saturated mouth), 36 (F2 ratio bias recentered to observed mean), 37 (mouth lingered after audio — silence-aware decay + explicit `'ended'`/`'pause'` listeners). Result: visible vowel-shape distinction (/i/-/e/ stretched, /u/-/o/ rounded, /a/ neutral open) with mouthY varying smoothly 0.3–1.0 instead of binary on/off. Forward-compatible if Fish Audio later exposes `char_timings`.

### Added April 30, 2026
- **Zani birthday dialogue (June 11)** — `Birthday: 11 June` added to ABOUT ZANI durable facts. Three new greeting arrays (eve/on-day/after) routed in `pickGreeting()`. Birthdays take precedence over absence and time-of-day.
- **Tiered absence detection** — sliding-window time tracking via localStorage `amadeus_last_seen`. Three tier arrays: `GREETINGS_SHORT_AWAY` (24-72h), `GREETINGS_MEDIUM_AWAY` (3-14d), `GREETINGS_LONG_AWAY` (14d+). Defensive try/catch wraps storage.
- **Greeting freshness memory** — new `pickFresh()` helper avoids back-to-back repeats. localStorage `amadeus_recent_greetings` tracks recent indices per array. Cap of 3 (or `floor(len/3)` for small arrays).
- **Sleep-hours awareness** — `GREETINGS_SMALL_HOURS` array for 01:00-04:59 (heavier concern register, split from NIGHT). New `formatTimeContext()` injects context note at end of system prompt during late-night hours, giving Kurisu permission to gently push back about Zani being awake. ~30 conditional tokens.
- **British date format** — Birthday displays as `11 June` not `June 11`. One-line change in ABOUT ZANI.
- **Three planning docs created** in `docs/`: `roadmap-rag-vn.md`, `roadmap-obsidian-mcp.md`, `roadmap-lip-sync.md` — for future Claude Code sessions. *(All three deleted August 2026 once the features shipped; their content now lives in this file, `bugs.md` and `session-log.md`. Historical note only — do not recreate.)*

### Added April 28, 2026
- **Stage 1 session memory** — sliding window of 7 most-recent diary entries injected into system prompt at runtime (`buildSystemPrompt()` in amadeus.html)
- **Diary-on-close coordinator** in main.js — auto-generates diary entry on app close (Cmd+Q OR X-button), runs Ollama from main process, saves via IPC. 40s outer timeout safety net (`DIARY_TIMEOUT_MS`; 12s per Ollama call). Both close paths route through shared `runDiaryWithExit()`. See bugs 28-30 for the design corrections.
- **IPC bridge** — preload.js exposes 5 channels: request-conversation, conversation-response, save-diary-entry, diary-save-complete, show-saving-overlay
- **"SAVING SESSION" overlay** — shown during diary work on close; sendMsg blocked while overlay visible (prevents concurrent Ollama call)
- **Variant B prompt** — replaces previous prompt; 25 casual examples, simple-words rule applies during emotional moments, ABOUT ZANI section with durable user facts, RECENT CONVERSATIONS caveat, he/him pronouns
- **Greetings rewritten** — 25 generic + 8×4 time-of-day, ~16% address Zani by name, only safe-emotion tags (no melancholic/thinking/embarrassed/flustered)
- **parsEmo with validEmotions Set** — strips ALL bracketed tags, only adopts known emotions
- **Fish Audio tag rewrites** — fragment grammar for `curious`, `thinking`, `melancholic`, `embarrassed`, `blush` (prevents English bleed)
- **IME/textarea fix** — `clearMsgInput()` helper with double-clear pattern, `e.isComposing` check
- **Hardcoded OLLAMA path** — same pattern as PYTHON, with defensive error handling

### Earlier (as of April 19, 2026)
- Boot video → Live2D transition
- Ollama gemma4:latest chat with streaming
- DeepL EN→JP translation (header auth)
- Fish Audio TTS (s2.1-pro since 2026-10-04, #221b) with neutral baseline voice
- 19-emotion system with rich voice actor direction tags
- Emotion-conditional prosody (breath sounds, pauses, openers per emotion)
- Dynamic speech speed via compute_speed() — 6 conditions
- Re-anchor tags between sentences (prevents tone drift)
- Audio-duration-based English subtitle sync — word reveal timed to exact audio duration
- Greeting sync on boot
- Live2D expressions + EMO_POSTURE for all 19 emotions
- Session diary (secret diary of conversations — faithful to the show)
- BGM
- Fish server auto-starts/stops with Electron app
- Flash attention (OLLAMA_FLASH_ATTENTION=1)
- Auto cache clear on launch
- Obsidian vault in docs/ for Claude Code memory
- Time-aware greetings (morning/afternoon/evening/night arrays already in place)
- Natural Live2D expression decay (emotions fade back to idle after emotion-appropriate duration)
- Special date dialogue on Kurisu's birthday July 25 (already implemented)

---

## Hardware Reality Check (cross-reference — April 16, 2026)

**Current stack constraints:** 16GB RAM MacBook Pro (Apple Silicon, MPS).
Any task requiring >~12GB of resident memory beyond OS + Electron + Ollama cannot run locally. (gemma4's resident cost is **~4.1 GiB**, not the 9.6 GB once quoted here — that was the on-disk file size. Measured 2026-08-26, see REFERENCE.md HARDWARE CONSTRAINTS.)

Legend:
- ✅ Feasible on current stack
- ⚠️ Feasible with caveats / lightweight variant recommended
- ❌ Impossible locally — requires cloud or hardware upgrade

| Goal | Tier | Status | Notes |
|---|---|---|---|
| Natural Live2D Expression Decay | 2 | ✅ DONE | Implemented April 19, 2026 (Bug 23 — investigation deferred April 28 + 30, code looks structurally correct) |
| Session and Across-Session Memory | 2 | ✅ DONE | **Stage 1 shipped April 28, 2026** — 7-entry sliding window. **Stage 2 shipped May 11, 2026** — rolled-up summary of older entries via Ollama on close, injected as LONG-TERM IMPRESSIONS block. Stage 3 (RAG over diary) deferred. |
| Special Date Dialogue (Kurisu birthday) | 2 | ✅ DONE | Already implemented |
| Special Date Dialogue (Zani birthday) | 2 | ✅ DONE | **Shipped April 30, 2026** — eve/on-day/after greetings, ABOUT ZANI birthday field |
| Tiered absence detection | 2 | ✅ DONE | **Shipped April 30, 2026** — short/medium/long away tiers via localStorage |
| Greeting freshness memory | 2 | ✅ DONE | **Shipped April 30, 2026** — `pickFresh()` helper avoids back-to-back repeats |
| Sleep-hours awareness | 2 | ✅ DONE | **Shipped April 30, 2026** — small-hours greetings + system prompt injection during 01:00-04:59 |
| Obsidian MCP Integration | 2 | ✅ DONE | **Shipped May 1, 2026** — `@bitbonsai/mcpvault` via `~/.claude.json`. Future sessions have direct read/write/search/append to all docs. |
| **VN Transcript RAG** | 2 | ✅ DONE | **Phase 1 shipped May 3, 2026** — dual corpus (JA voice clips + EN LP lines), bge-m3 embeddings, ChromaDB, Flask port 5003, health-poll window open. See `session-log.md` May 3 entry. |
| Ollama Translation (revisit) | 2 | ✅ DONE | **Shipped July 19, 2026** — solved with no extra RAM by reusing the resident gemma4 (`translate_via_gemma()`), not a dedicated ≤2B model. See the Tier 2 entry below. |
| Lip Sync | 3 | ✅ DONE | **Shipped May 2-3, 2026** — Web Audio API amplitude (peak time-domain) + formant analysis (F1/F2 ratio) drive `ParamMouthOpenY` and `ParamMouthForm`. Writes via `internalModel.on('beforeModelUpdate')` to override the idle motion. Visible vowel-shape distinction. See bugs 31-37 for the design history. |
| Faster Response Time | 3 | ✅ DONE | **Shipped May 15-16, 2026** — see Tier 3 entry below. |
| Whisper.cpp for Voice Input | 3 | ✅ | tiny/base/small models fit easily |
| Incoming Call Mode + Notifications | 3 | ✅ | No memory cost |
| UI Identical to S;G 0 | 3 | ✅ | Pure frontend |
| Amadeus Internet Research | 3 | ❌ | **Attempted June 2026, removed — see the detail section below.** This row read ✅ until 2026-09-04, contradicting that section. Verified against the code that day: `fetchWebContext`, `needsWeb` and `/web-search` have **0 hits** in `amadeus.html` and `kurisu_rag_server.py`, and git has never contained them (the feature predates the July 13 baseline commit). **She has no live outside-world knowledge today.** |
| **Fine-tune LLM on S;G VN Transcript** | 3 | ❌ | **Local fine-tuning of a 12B model needs ~40–60GB RAM/VRAM. Impossible on 16GB Mac. RAG (above, shipped Tier 2) is the recommended alternative.** |
| **Fine-tune Voice on VN Dataset** | 3 | ❌ | Already flagged — local S2 weights need ~20GB RAM. Cloud GPU or Fish Audio platform submission required. |
| Live2D Model Replacement | Last | ✅ | Asset swap, no memory cost |

### Lightweight alternatives for flagged (❌) items

**Instead of full LLM fine-tune on VN transcript:**
- **RAG approach** — ✅ DONE (May 3, 2026). Dual-corpus ChromaDB with bge-m3, k=3 per collection.
- **LoRA adapter via cloud** — if true fine-tuning is wanted later, rent a single A100 hour on Runpod/Lambda (~$2), train a small LoRA adapter on the VN transcript, then load the adapter on top of gemma3:12b locally at inference. Adapter load cost is negligible.
- **Prompt engineering only** — hand-curate 30–50 of the most characteristic Kurisu lines as few-shot examples in the system prompt. Cheapest path, often underrated.

**Instead of local voice fine-tune:**
- Already covered in existing roadmap entry — Fish Audio platform submission (hosted) or cloud GPU for local S2 training. No change needed.

---

## Tier 2 — Next Priority

### ✅ DONE: Stage 1 Session Memory (April 28, 2026)
- Sliding window of 7 most-recent diary entries injected into system prompt at runtime
- Diary entries auto-generated on app close via main.js coordinator (Cmd+Q OR X-button)
- Reset button still works as manual save
- See `REFERENCE.md` for architecture, `bugs.md` 28-30 for design history

**✅ Stage 2 shipped May 11, 2026:** when diary entries exceed 7 (the sliding window), older entries are rolled up into a Ollama-generated summary on app close. Stored in `amadeus_diary_summary` + watermark. Injected as LONG-TERM IMPRESSIONS block before RECENT CONVERSATIONS in the system prompt. Bounded token cost forever regardless of total entry count: `num_predict: 180` (raised from 100 on 2026-08-26 — at 100 it truncated 63% of the time, bugs.md 70) yields ~105 tokens median, 132 max measured over 30 runs on a worst-case 43-entry input.

**Future memory upgrades if needed:**
- **Stage 3 (RAG):** vector retrieval from full diary corpus. ✅ Shipped May 11, 2026 as RAG Phase 2 (`amadeus_diary` collection) — see the Phase 2 entry below.

### ✅ DONE: Zani birthday dialogue (April 30, 2026)
- ABOUT ZANI section now contains `Birthday: 11 June` (British format)
- Three greeting arrays (eve/on-day/after) with date checks in `pickGreeting()`
- Birthdays take precedence over absence detection and time-of-day

### ✅ DONE: Tiered absence detection (April 30, 2026)
- Sliding-window time tracking via localStorage `amadeus_last_seen`
- Three tier arrays for 24-72h / 3-14d / 14d+ gaps
- Defensive try/catch wraps storage; never crashes greeting flow on corrupt data

### ✅ DONE: Greeting freshness memory (April 30, 2026)
- New `pickFresh()` helper avoids back-to-back repeats across launches
- localStorage `amadeus_recent_greetings` tracks recent indices per array
- Cap of 3 (or `floor(len/3)` for small arrays — formula prevents over-blocking)

### ✅ DONE: Sleep-hours awareness (April 30, 2026)
- `GREETINGS_SMALL_HOURS` array for 01:00-04:59 (heavier concern register, split from NIGHT)
- New `formatTimeContext()` injects context note at end of system prompt during late-night, giving Kurisu permission to gently push back
- ~30 token cost, only during 01:00-04:59

### ✅ DONE: Obsidian MCP Integration (May 1, 2026)
`@bitbonsai/mcpvault` connected to Claude Code via `~/.claude.json`. All 9 docs now readable/writable/searchable inline from any Claude Code session. See `session-log.md` May 1 entry for troubleshooting notes (3 issues hit: wrong env var, wrong PATH, wrong config file).

### ✅ DONE: VN Transcript RAG — Phase 1 (May 3, 2026)
Dual-corpus ChromaDB with bge-m3. See `session-log.md` May 3 entry.

### ✅ DONE: RAG Phase 2 — Diary Corpus Integration (May 11, 2026)
Third ChromaDB collection `amadeus_diary` adds semantic recall of older conversations by topic. Three memory layers now active: LONG-TERM IMPRESSIONS (Stage 2 summary) + RECENT CONVERSATIONS (Stage 1 window) + RELEVANT PAST MOMENTS (Phase 2 diary RAG). See session-log.md May 11 entry.

### ✅ DONE (differently than planned): Ollama Translation — July 19, 2026
Original plan: replace DeepL with a small dedicated local translation model for more natural
Japanese, hard-constrained to ≤2B params and pre-loaded via keep_alive to avoid cold-start
OOM against gemma4:latest.

**What actually shipped:** no second model at all. `translate_via_gemma()` uses the
**already-resident gemma4** with a register-aware Kurisu prompt (temp 0.3, num_ctx 8192),
which costs zero extra RAM — the constraint that killed the original approach. A/B verdict
7/8 in its favour. `TRANSLATOR='gemma4'` at the top of `kurisu_fish_server.py`; set it to
`'deepl'` to revert. DeepL remains the fallback path only.

*Known cost, accepted:* each translate call is ~0.66s of 100%-GPU time shared with her
Live2D rendering — the measurement behind bugs.md 61.

---

## Tier 3 — Future

### ✅ DONE: Faster Response Time — First-Message Lag (May 15–16, 2026)
Cold-load lag on first message (5–10s, Live2D stutter) fully eliminated across two sessions.

**May 15 — initial prewarm:**
- `prewarmOllama()` added to `amadeus.html` — fire-and-forget chat call during boot video dead time, `num_predict:1`, `think:false`, `keep_alive:'30m'`
- bge-m3 evicted after diary indexing (`keep_alive:0`) — frees ~1 GB

**May 16 — root cause fixed (num_ctx mismatch + race condition):**
- `prewarmOllama()` was sending no `num_ctx`. `sendMsg()` sends `num_ctx:8192`. Ollama allocates a KV buffer per `num_ctx` value — different sizes = different buffer = guaranteed cache miss on every first message. Fix: added `num_ctx:8192` to prewarm, and replaced `'hi'` with `buildSystemPrompt('')` so the full system prompt prefix is in cache before user types.
- `prewarmOllamaMain()` added to `main.js` — polls Ollama, loads gemma4 into RAM during the 5s pre-window delay before `createWindow()` opens. AbortController cancels it at exactly 5s, preventing a stale request from arriving after the renderer's system-prompt prewarm and evicting the KV cache.
- `Promise.all([waitForHttpServer(), 5s timer])` guarantees minimum 5s window even on warm relaunch (server ready in ~200ms otherwise).
- Net result: first-message lag eliminated; Live2D stutter gone; `HISTORY_WINDOW=30` added to cap history sent to Ollama at 15 exchanges without affecting diary generation.

**Remaining latency work (if ever needed):**
- Per-token generation speed still bound by model size. Candidates: smaller model (gemma4:4b?), quantisation (Q4_K_M → Q3_K_S), speculative decoding (needs draft model — RAM pressure on 16 GB)
- Research fresh — this field moves quickly

### ✅ DONE: Voice Input — MLX Whisper (May 10–11, 2026)
Replaced Web Speech API stub with MLX Whisper medium (`mlx-community/whisper-medium-mlx`). Toggle record → spinning-dots indicator → transcript review → Send. New `kurisu_whisper_server.py` on port 5004; `threaded=True` Flask with background model warmup; ffmpeg PATH fix; 30s AbortController timeout. BGM protected via `bgmInterrupted` flag during audio session switches. Boot video fixed: `ensureAudioContext()` now called before `playBootVideo()`. CoreAudio gap timer (3s) in main.js prevents AUDIO_RENDERER_ERROR on quick relaunch.

### ✅ DONE: Lip Sync (May 2-3, 2026)
Web Audio API amplitude analysis + formant analysis driving Live2D `ParamMouthOpenY` and `ParamMouthForm`. Single-file change to `amadeus.html`. Forward-compatible if/when Fish Audio adds `char_timings`.
- **Pipeline:** `createMediaElementSource(audio) → AnalyserNode (fftSize=256, smoothingTimeConstant=0.3) → audioCtx.destination`. RAF reads time-domain peak amplitude (smoothing factor 0.8 attack / 0.55 silence-decay / 0.18 normal-decay) and FFT magnitude data each frame.
- **Vowel detection:** F1 band (bins 1–5, 172–862 Hz) energy vs F2 band (bins 7–17, 1206–2929 Hz) energy. Ratio recentered at 0.25 (observed mean for speech) and amplified ×3.5 to spread vowels across the form parameter range.
- **Override path:** `live2dModel.internalModel.on('beforeModelUpdate', ...)` — direct ticker writes were silently overridden by the idle motion every frame; the `beforeModelUpdate` event fires after all motion/expression/breath/physics updates and before `coreModel.update()` bakes parameters into the mesh.
- **Calibration:** AMPLITUDE_GAIN=3 linear (peaks 0.10–0.30 → mouthY 0.30–0.90), VOWEL_FORM_SCALE=0.7, IDLE_FORM=−0.49, sharper speech/idle blend (`min(1, mo×2)`).
- **Mouth-close after audio:** explicit `'ended'`/`'pause'` listeners on the `<audio>` element trigger `fadeMouthClosed()` (100ms) immediately, not waiting for the next RAF tick to detect `audio.ended`.

### ✅ DONE: Incoming Call Mode + Desktop Notifications (May 12, 2026)
Amadeus calls the user randomly, like in the show.
- Scheduler: `amadeus_scheduler.json` persists one random time per day in [13:00–21:00]. Reuses existing pick if app reopened same day. Marks `callFired: true` when it fires.
- Call fires when mainWindow is not visible (e.g. minimized). If visible, skips for the day.
- Always-on-top 340×580 frameless `call-window.html` with smartphone UI: circle-cropped logo, red pulsing glow, caller name/subtitle, decline (red) + accept (green) buttons, 30s countdown auto-dismiss.
- `preload_call.js` exposes only `callAPI.accept()` and `callAPI.decline()`.
- Accept path: if main window exists → show + focus + `incoming-call-accepted` IPC → special greeting. If not → `?incomingCall=1` URL flag → boot() skips video, goes straight to reveal + `GREETINGS_INCOMING_CALL`.
- Decline / timer expiry → close call window only, no other effect.
- Native Notification shown if supported (unsigned app may suppress; call window always opens).
- `GREETINGS_INCOMING_CALL` (4 entries, safe emotions: tsundere/surprised/calm). Uses `pickFresh()` for repeat avoidance.

**Architecture update (May 12, 2026 — follow-up session):** Scheduler extracted from `main.js` into `AmadeusCall.app` — a separate background Electron app in the `scheduler/` directory. Ships alongside `Amadeus.app` in `dist/mac-arm64/`. Key properties: runs as a login item (`app.setLoginItemSettings({ openAtLogin: true, openAsHidden: true })`), hidden from dock, stays alive after call window closes. Call-fire check changed from `mainWindow.isVisible()` to `pgrep -x Amadeus` (whether the main app is running at all). Bugs fixed in same session: `appReady` guard (bug 47) prevents BrowserWindow crash in `second-instance` handler; `scheduleHourlyCheck()` loop (bug 48) limits macOS sleep drift to ≤1 hour; `callTimerSet` flag (bug 48) prevents timer stacking. **Tested and confirmed stable — no bugs found.**

### ✅ DONE: Relationship Depth Arc (June 2026)
Kurisu's warmth shifts over accumulated sessions — early sessions sharper/more tsundere, later sessions warmth slips through more easily. Item 1 of the Claude-chat "less boring" list. Implicit by design (no visible meter). All in `amadeus.html` (relaunch only).

- **5 stages** keyed to a cumulative score: Guarded (0) → Thawing (5) → Familiar (15) → Close (35) → Bonded (65). Thresholds `REL_STAGE_THRESHOLDS=[0,5,15,35,65]`.
- **Engagement-weighted scoring:** +0.5 base per *genuine* new session (gap ≥30 min) applied on the **first exchange**, not at boot — so opening and closing without chatting earns nothing. Plus +0.05 per exchange capped at +1.0/session. Net 0.5–1.5 per active session → ~65 sessions to Bonded (slow / earned pacing).
- **Stage frozen at boot** (`initRelationship()`, before `prewarmOllama()`) so the directive text is byte-identical all session → preserves the prewarm KV-cache prefix (bugs 33/34). Score keeps growing live in the background; stage only re-reads next boot.
- **Directive injection:** `relationshipDirective()` returns a stage-specific `RELATIONSHIP` block injected before the `TWO MODES` anchor in `buildSystemPrompt()`. Each stage anchors what does NOT change (tsundere nature, deflection reflex, covering warmth) and only shifts how easily/often warmth slips.
- **First-run seed:** `Math.min(seedSessions, 34)` from existing diary history — capped at Familiar so long-time users don't jump straight to Bonded.
- **Mild reunion coolness:** absence ≥14 days drops one stage at boot, but only if stage ≥2 (a new/Guarded relationship can't get colder).
- **State:** localStorage `amadeus_relationship = {score, sessions, sessionExchanges}`. Live accrual via `bumpRelationshipEngagement()` after each reply in `sendMsg()`.
- **Debug:** `window.showAmadeusRelationship()` in DevTools → console.table of stage/score/progress.
- **Bug fixed alongside:** incoming-call boot path and in-session incoming-call handler never wrote `amadeus_last_seen` (previously only `pickGreeting()` did) — affected both absence greetings and reunion-coolness detection. Now written in both.
- **Current state:** score 34.5 = Stage 2 (Familiar), 0.5 from Close.

### ✅ DONE: Diary reflections reflect relationship stage (June 15, 2026)
Follow-up #2 to the relationship arc. Previously the diary was generated with the *bare* diary prompt, so at any stage her private nightly reflections were written in the same Guarded-default voice. Now `buildDiarySystemPrompt()` (renderer) appends a stage-specific voice modifier to the base diary prompt. The private arc is about her internal *honesty with herself* (clinical/suppressed at Stage 0 → tender/guard-down at Stage 4), distinct from her chat-facing performance.
- Both diary paths covered: `generateDiaryEntry()` (renderer inline, Reset button) calls it directly; the diary-on-close IPC path now passes `diarySystemPrompt` in the `conversation-response` payload, and `main.js` uses it with the old hardcoded string as a safe fallback.
- `amadeus.html` relaunch + `main.js` rebuilt.

---

## Tier 2.5 — "Less Boring" Feature Backlog (Claude-chat list, June 2026)

Source: Claude-chat assessment of why Amadeus felt passive. Item 1 (relationship arc) shipped. Remaining items below, roughly high→low impact. **Next chat: pick from here.**

### Relationship-arc follow-ups (from the post-implementation review)
- **#1 — Empirically verify tone shift across stages — ✅ DONE (June 19, 2026).** Built an offline harness (`dev/stage_compare.py`) that fires a fixed 5-probe set (compliment / vulnerable / affection / Dr Pepper / a neutral science CONTROL) at gemma4 using the byte-exact per-stage system prompt, 5 samples each, side-by-side output. **Finding:** the arc *does* work — gemma4 is not ignoring the directive — but v1 was gentle and uneven (affection barely moved, the most important emotional probe). **Root cause (the real insight):** the directive is squeezed between the base-prompt warmth floor (line ~401 "real friendship, care about his day/meals/sleep") below it and the ROMANTIC/FEELINGS + INPUT→EMOTION hard rules above it — NOT burial/wording. Reworded the 5 `relationshipDirective()` strings to move only the FREE variables (deflection flavour: flat denial → fond transparent cover; tail: redirect-away → warm callback), leaving tags and the mandatory stammer/deflect structure untouched, and keeping the warm floor (Zani's explicit call). **v2 result:** affection now shifts cleanly within the hard rule (Guarded "focus on your own stuff" → Bonded "I noticed you weren't around. Did you get any work done on your rhythm games?"); vulnerable + Dr Pepper endpoints clearly distinguishable; CONTROL stayed flat `[lecture]` with zero callback bleed. Caveat: 0→2→4 ordering isn't perfectly monotonic under temp 0.85 (5 samples), but the 0↔4 endpoints are reliably distinguishable — enough to be perceptible in practice. Baselines saved at `dev/stage_comparison_v1_baseline.md` / `_v2.md`.
- **#3 — `window.setAmadeusStage(n)` dev helper — ✅ DONE (June 19, 2026).** Shipped in `amadeus.html`: `setAmadeusStage(n)` (live in-session stage override, warns it breaks the KV-cache freeze, never touches localStorage score), plus `dumpSystemPrompt(n)` (returns the byte-exact prompt for a stage) and `dumpStagePromptsToFile([0,2,4])` (downloads the prompt bundle the harness reads). Reusable for any future directive tuning.

### Remaining feature ideas (items 2–7)
2. **Mid-session proactive messages** — ✅ DONE (June 20, 2026). Generated through the full system prompt (temp 0.9, num_predict 80) for true variety; pickFresh rotates the nudge type (6 modes); cap 2 nudges + escalating 2-min delay; abortable on any activity; visibilitychange pause; tested via fireProactiveNow(). Does not bump engagement.
3. **Topic-tagged diary recall** — RAG currently surfaces past moments generically. Add a tagging layer on diary entries (topics: chess, 音ゲー, football…) so she can callback specifically ("how did that game go?"). ChromaDB infra already exists.
4. **Calendar / exam-period context injection** — she knows the date; extend so A-level exam period → notices Zani is stressed without being told, asks how revision is going; week after → asks how it went. Scheduled context injection at the system-prompt level, no fine-tuning.
5. **Voice-first mode** — Whisper is already integrated. Speak → she responds with voice → mic re-activates automatically. No typing. Qualitatively different experience.
6. **Shared "activities" / Dr Pepper moments** — ✅ DONE (June 20, 2026). Curated 10-line pool via pickFresh + 10-min cooldown, bypasses LLM. gemma4 inverts the canon (treats Dr Pepper as Zani's gross soda) — curated lines guarantee the intellectual beverage phrasing. Served in sendMsg try-block before RAG/ollamaStream; bumpRelationshipEngagement included.
7. **Progress / secret unlockables** — hidden lines that appear only after X sessions or a certain relationship stage (now that the arc exists, this can key off `_relActiveStage`). The Steins;Gate VN used earned-moment reveals well.

**Deferred / low-priority:** shared media reactions, her having opinions on things Zani tells her (football results, rhythm-game scores). A *visible* relationship-stage indicator was explicitly rejected — implicit is better.

---

### UI Identical to S;G 0
Pixel-accurate recreation of the Amadeus terminal UI from the visual novel.
- Includes post-boot sound effects and visual effects
- Research S;G 0 screenshots/footage extensively before starting

### Amadeus Internet Research — ⚠️ attempted, approach abandoned
Amadeus searches the internet to answer questions or reference current events.
- **Attempted (June 2026):** DuckDuckGo instant-answer scraping via `duckduckgo_search` Python library. Results were unreliable (wrong/outdated answers), introduced 1-2s lag per message, and caused the model to generate confidently incorrect responses about recent events. Removed entirely.
- **If revisited:** needs a proper search API (Perplexity, Tavily, or similar) with structured results, not raw scraping. Also needs tighter injection logic so search context doesn't pollute casual conversation turns.

### Fine-tune LLM on S;G VN Transcript (text responses) — ⚠️ RE-COST BEFORE ACTING
Make Kurisu's text responses more authentically Kurisu using her VN dialogue lines.
> **⚠️ The analysis below is STALE in two ways (flagged 2026-08-26).** It was written against
> **gemma3:12b**; the app has run **gemma4:8b (Q4_K_M)** since July. And its "16GB Mac" premise
> used the old ~9.6GB anchor, which backlog #172 showed was the model's **disk** size — the real
> resident cost is **4.10 GiB RSS**. An 8B QLoRA is a materially different proposition from a
> 12B full fine-tune and may be locally feasible. **Re-cost it before quoting these numbers.**
>
> **Also read bugs.md 76 first.** Her most-repeated catchphrase, *"Don't get the wrong idea"*,
> appears **nowhere** in the 1,672-line VN corpus — it came from our own SYSTEM_PROMPT quoting
> it twice, and removing it took the rate 37% → 3%. That is direct evidence that some of the
> "doesn't sound like the show" gap is **prompt-induced and free to fix**, not a model-capability
> limit. Measure which portion is which before spending on a LoRA.
- **Full fine-tune of gemma3:12b impossible on 16GB Mac** — needs ~40–60GB RAM/VRAM
- **Recommended path (shipped as Tier 2):** RAG with embedded VN transcript. Phase 1 shipped May 3, 2026; Phase 2 (diary corpus) shipped May 11, 2026.
- **If true fine-tune wanted later:** rent ~1 hour cloud GPU (A100 ~$2 on Runpod/Lambda) for a LoRA adapter — load adapter locally at inference time, negligible memory overhead
- **Cheapest alternative:** hand-curate 30–50 iconic Kurisu lines as static few-shot examples in system prompt (already partially achieved by Variant B's 25 casual examples). Note the KV-cache cost: examples are ~31% of a ~2,450-token prompt (backlog #156), and per bugs.md 76 examples are also what she actually copies — so curating them is a high-leverage lever in BOTH directions.

### Fine-tune Voice on VN Dataset — ❌ not feasible locally
Use the 756-clip dataset to train a proper voice model rather than zero-shot cloning.
- Location: ~/Documents/Kurisu_Dataset_Pro/ (756 WAV clips + metadata.csv)
- **Local fine-tuning of S2 weights impossible on 16GB Mac** (~20GB RAM required)
- Two viable paths: Fish Audio platform submission (hosted), or cloud GPU for local S2 training
- Research Fish Audio dataset submission process fresh in June — S2 launched March 2026, pipeline still evolving
- Check: https://docs.fish.audio and https://github.com/fishaudio/fish-speech

---

## Voice — her tsundere/flustered voice (backlog #221 / #221b)
- **Fish s2.1-pro + `prosody {"volume": -1.0}`** — ✅ KEPT 2026-10-04 (Zani: *"I like her voice now. It's good."*). Shipped for a live trial 2026-10-04 (tag `pre-221b`). Blind A/B by Zani:
  Stage 1 18/18 current clips "too calm"; 2a 15-1; 2b 14-1-1 + guard 16-0; Stage 3 (paid) 8/8 fine. Costs: ~0.5s more per reply,
  pitch ~2 st higher and more variable (a lower temperature made it worse, 2c). Mark ✅ only if Zani keeps it.

## Voice — opener variety (backlog #180)
- **Opener variety, arm Q0** — ❌ TRIED AND REVERTED (shipped Sep 19, reverted Sep 22, 2026). Zani:
  her tone was *"way too calm"* on emotional lines, and he preferred her voice before. Offline metrics
  had passed every guard and did NOT predict it (see bugs.md 90). Original trial notes: Shipped to `amadeus.html` for Zani's live
  test: the copied tame exemplar lines removed, and one banter-consent paragraph added at the top of
  ROMANTIC/FEELINGS. Measured offline: 11 distinct first words vs 6, widest repeated phrase 5 vs 9, prompt
  copies 0 vs 11, same length, 0 names in daily/sad chat. The heat Zani asked for (pervert/idiot/dummy on
  teasing lines) did NOT ship — gemma4's ceiling was ~4/17. Revert: `git checkout pre-q0-ship -- amadeus.html`.
  Mark ✅ only if Zani keeps it.

## Last (after everything above)

### Live2D Model Replacement
Replace current model (similar to VN Kurisu) with one closer to the Amadeus anime/show version.
- Tool found: see-through (https://github.com/shitagaki-lab/see-through) — generates ready-to-rig PSD file
- Do not start until all improvements above are complete

---

## Dataset
- Location: ~/Documents/Kurisu_Dataset_Pro/ (corrected from ~/Desktop/ — actual path)
- Files: kurisu_0000.wav to kurisu_0755.wav (756 clips)
- Transcript: metadata.csv (pipe-separated: filename|japanese_transcript, no header row)
- Status: **Phase 1 RAG ACTIVE** — embedded in `kurisu_ja` ChromaDB collection

## Subscription Note
- Fish Audio Plus plan ($11/month) — expired April 16, 2026
- Renew before resuming voice work in June
