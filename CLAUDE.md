# AMADEUS — Kurisu Makise AI (Steins;Gate 0)
# Electron macOS app · Zani (zha61, he/him) · M5 MacBook Pro 16GB RAM
# Last updated: September 30, 2026 (bugs.md 97 — #205 Whisper repetition gate)

## ZANI'S STANDING INSTRUCTIONS — read these before anything else

### 1. Write to Zani in ASD-STE100 Simplified Technical English. Every reply, every session.
- Keep sentences to 25 words or less. Use the active voice. Write one instruction per sentence.
- Use the same word for the same thing. Do not use synonyms.
- Use a vertical list when there is more than one item.
- **Apply it HARDEST on technical content** — measurements, root causes, trade-offs. That is
  when he needs it, and that is when it gets dropped. The failure mode is real and repeated:
  comply for three messages, then revert the moment a measurement is reported.
- **Scope:** this is about how you WRITE TO ZANI. It is not a rule for the source code, and it
  is NOT a rule for Kurisu's dialogue. Her voice comes from `SYSTEM_PROMPT` and
  `docs/kurisu-personality.md`. Never apply STE to her lines.

### 2. DO NOT CHANGE HOW HER TEXT AND AUDIO APPEAR ON SCREEN. (2026-09-07)
The word-by-word reveal, timed to her audio, is **finished work and it is what he wants.**
He said it plainly: *"the Amadeus before was great."*
- **Forbidden without him asking first:** the subtitle reveal, its timing, the `...` placeholder,
  the thinking dots, when text appears relative to her voice, and how audio is delivered.
- **Already rejected, do not re-propose:** streaming her text to the screen as she writes it
  (would have cut the felt wait ~4.8s → ~1.0s, but it lets him read the line before she says it —
  he chose the character over the speed); and the P4 thinking indicator (bugs.md 81/82 — it broke
  her reply text AND he did not want it).
- **This rules out backlog #188 (P3 streaming TTS) as designed**, because per-sentence synthesis
  breaks the audio-duration subtitle sync (bugs.md 6). Do not start it.
- **STILL WANTED: make her reply FASTER without losing quality.** Everything below the display
  layer is open — see the handoff in `session-log.md` for the ranked list. **The translate step
  is CLOSED (2026-09-07, backlog #196): all four arms measured and rejected, it is 77% decode.
  The top item is now the per-turn RAG block at +533ms of prefill every turn (#160).**

### 3. HER REPLY LENGTH IS FINE AS IT IS. Do not shorten it. (2026-09-07)
Zani, unprompted, after seeing the measurement: *"I think now the way she talks is fine, like
the sentence length."*
- **Do not ship #176's length instruction, or any variant of it.** The arm WORKS — it takes her
  ≤8-word replies from 0.0% to 50.0% (canon is 50.8%) and saves ~750ms/turn. **He does not want
  it.** This is a taste decision and it outranks the canon metric, exactly as the display freeze
  outranked a 4.8s latency win.
- **The canon-likeness gap on LENGTH is therefore CLOSED BY DECISION, not by engineering.**
  `dev/canon_likeness.py` will keep reporting W≈8.8 words and 0% ≤8-word replies. That is now
  the intended state. Do not re-open it as a defect.
- **What this does NOT close:** her VOCABULARY and PHRASING (bugs.md 76/77, backlog #180) are
  separate axes and were never part of this decision. An exemplar swap changes phrases, not
  shape — do not reason from one to the other (CLAUDE.md 45/46).
- **Speed consequence, stated so nobody re-derives it:** shorter replies were the only remaining
  lever on the translate step (decode is 77% of it and scales with tokens). With this closed,
  the per-turn RAG block (#160) was the next candidate — **but it was decomposed on 2026-09-07
  and its +533ms is NOT an available saving.** Only ~37ms is free (moving static headers into the
  cached system message); the sizeable ~160ms requires trimming her retrieved diary entries.
  **There is no large quality-free speed win left. Every remaining lever costs her length, her
  memory, or her register — all three of which Zani has said he values.**
- 🛑 **THE SPEED WORK IS STOPPED BY ZANI (2026-09-07).** Shown the full table — translate closed,
  length declined, RAG diary trim at ~160ms costing her memory, RAG headers at ~37ms — he said
  **"stop here."** **Do not reopen the latency effort unprompted.** The measurements are all in
  backlog #196 and #160 and stand ready if he ever asks again. If he raises slowness in future,
  ASK what specifically feels slow before proposing anything — the one time it was inferred from
  a number instead of asked, it produced P4, which shipped, broke her reply text and was reverted
  (bugs.md 81/82).

### 4. HER OPENERS AND HER "HEAT" ARE CLOSED. Do not re-open backlog #180. (2026-09-22)
Seven weeks of work, 13 measured arms, five mechanism families, two blind A/B tests by Zani, one
live trial — **and nothing shipped.** The one version that reached the app was reverted by him after
three days: *"her tone sounds way too calm"*, *"I feel like I like her voice before"* (bugs.md 90).
- **The prompt he has liked all along is the one in `amadeus.html` now** (`pre-q0-ship`). Leave it.
- **Do not re-run any of it:** rewriting her exemplars, a forming rule for the deflection, the emotion
  tag at the end of the reply, consent framing for banter, or example conversations before the history.
  Every one is measured and recorded in backlog #180; the arms are in `dev/opener_arm.py` on `main` (merged from `fix-180` on 2026-09-22; tag `180-closed`).
- **What was proven, so nobody re-derives it:** the emotion tag picks her opening word
  (`[flustered]`→"what" 65%, `[tsundere]`→"don't" 82%); anchoring her opener on HIS words makes her
  echo him; removing the anchor brings "W-what" back; **gemma4 will not call Zani names** — the ceiling
  was 4 of 17 teasing replies across every method tried.
- **If HE raises it again:** ask what specifically sounds wrong, and read CLAUDE.md 53 first — for tone,
  metrics can only reject a version, never approve one. His ear in a short live trial is the only gate.
- **Still open and NOT covered by this:** her long-term memory, the diary, and anything below the
  display layer that does not change how she sounds.

## Working principles
- **World-class, machine-safe — standing order (July 18, 2026)**: every implementation must match best-in-class practice for the feature (research SOTA first) AND fit the M5/16GB resource budget. **The anchor is gemma4 = ~4.1 GiB RESIDENT** (`llama-server` RSS, measured 2026-08-26, stable under load, `num_ctx:8192`). The old "~9.6GB" figure was the **on-disk file size** (`ollama list` reports 9.6 GB = 8.95 GiB) being used as a RAM budget — the model is mmap'd, so disk size is not residency. State RAM/CPU cost of new components before building, and say WHICH number you mean.
- **Think before coding** — state assumptions, surface concerns BEFORE writing code


- **Simplicity first** — touch only what the task requires, don't refactor opportunistically
- **Surgical changes** — small targeted edits over rewrites; preserve working code
- **State a plan** — for non-trivial changes, share the plan and get approval before coding
- **Update docs after EVERY implementation — not at session end.** A change is not
  finished until the docs match it. Do not batch this: a long session gets summarized
  before you get to it, and a session that ends abruptly never gets to it at all.
  Docs land in the SAME commit as the change they describe, so a revert takes both.
  1. **Reconcile, don't just append.** A session-log entry is NOT enough. The drift
     that keeps biting us is a changed value left stale in a reference doc.
  2. **Grep the OLD value, never the new one.** Searching for the value you just
     wrote can never find the stale copy still sitting in another file. Every doc
     that states a value you changed must be fixed in the same pass.
  3. **Route by kind:** bug found AND fixed → bugs.md (+ a CLAUDE.md rule if it is a
     trap worth blocking); found but NOT fixed → improvements-backlog.md; feature
     shipped → roadmap.md ✅; what happened → session-log.md, INSERTED under the
     handoff block (the file is reverse-chronological — "append" buries it below
     April).
  4. **Before you stop:** refresh the handoff block at the top of session-log.md —
     it is the first thing the next session reads.

### Verification discipline
- Before describing or editing any function, grep/view its CURRENT definition
  in the actual file and quote the real signature — never describe behavior
  from memory of a past session or an earlier point in this conversation.
- When explaining WHY something works a certain way, cite the specific file
  and line. If you cannot point to the line, say so explicitly instead of
  answering from inference.
- For any change touching Ollama, TTS, IPC, or Electron lifecycle timing:
  do not claim it's fixed based on reasoning alone — state that it needs a
  live relaunch test, and say so before I confirm it worked.
- After any edit, explicitly check the diff against bugs.md by rule NUMBER
  (not vibe) — list which numbered rules are relevant and confirm none are
  violated.
- On long sessions: if this conversation has covered many unrelated fixes,
  flag it and suggest starting a fresh session once docs are updated, rather
  than continuing to build on an increasingly summarized context.

## Commands
- `npm run check` parses `main.js`, `preload.js` and `preload_call.js` too (added Aug 26,
  2026 — backlog #170). Before that it did not, and would say "safe to relaunch" for a
  broken main process. The hand-run `node --check main.js` workaround is no longer needed.
- **Check BEFORE every relaunch:** `npm run check` — parses amadeus.html's inline script
  (catches the duplicate-`const` class, rule 3, in ~1s), compiles the python servers, and
  asserts the SYSTEM_PROMPT injection anchors still exist. Exit 1 = do not launch.
- **Prove the checker still works:** `npm run check:selftest` — mutation test. Plants 3
  known bugs plus 1 that must NOT be reported, on sandboxed copies. Run it after you edit
  `dev/check.js` or upgrade Node. Green = `npm run check` still has teeth.
- `node dev/facts_close_test.js` — 29 checks + 3 mutants (bugs.md 92). The OUTCOME check: after a close with a fact in
  the reply, the fact is IN `amadeus_facts_v1`. Run it after touching `extractFactsNow`, `_parseFactsJson`, `mergeFacts`,
  the `onRunFactsExtraction` handler or main.js Step 5. Also run `node dev/facts_abort_test.js` (15).
- `node dev/log_sink_test.js` — 33 checks + 5 mutants (bugs.md 93/94), ~36s — check 9 runs the REAL Electron
  (hidden window, ~150 MB while it runs; the listener must take ONE parameter, bugs.md 94). Run after touching `spawnLogged`,
  `childStdio`, `installMainLog`, `attachRendererLog` or any spawn in main.js.
- `node dev/diary_close_index_test.js` — 8 checks + 3 mutants (bugs.md 95). Run after touching the
  `onSaveDiarySummary` handler or the boot `indexDiaryInBackground()` calls. Nothing may index at close.
- `node dev/unload_log_test.js` — 6 checks + 3 mutants (bugs.md 94), <1s. Run after touching `beforeunload`, `initBGM`'s
  `onerror` or the `[BootVideo]` trail. `_pageUnloading` must be set FIRST in `beforeunload`.
- **Logs (bugs.md 93):** `data/logs/{fish,http,rag,whisper,main,renderer}.log` (+ `.1`). Read these FIRST when
  something failed silently. Renderer log drops only `[LipSync] peak:` / `[LipSync ticker]` info lines.
- `node dev/whisper_gate_test.js` — 12 checks + 3 mutants, and `python3 dev/whisper_server_test.py` — 4 checks
  (bugs.md 97). Run after touching `hfHandleUtteranceBlob`, `hfRepeatRun`, the `HF_*` gate constants or `/transcribe`.
- `node dev/facts_refresh_rank_test.js` — 7 checks + 3 mutants (bugs.md 96). A memory-panel add/edit/delete must
  re-select facts with the BOOT ranking (`initFacts`). Run after touching `initFacts`, `_factRank` or `_memoryRefreshActive`.
- `node dev/facts_age_test.js` — 19 checks + 3 mutants (backlog #216). Proves the prompt is BYTE-IDENTICAL to
  `bbb0c8b` for facts under 30 days old, and that a 30+ day undated fact carries `[learned over … — it may have changed]`.
- `node dev/greeting_cache_test.js` — 5 checks (bugs.md 91). Every greeting must be READ from the file the
  writer SAVES. Run it after touching `greetingCacheKey`, the `amadeus-asset` handler or the cache writer.
- **Launch:** `open ~/Documents/Amadeus/dist/mac-arm64/Amadeus.app`
- **Rebuild (main.js/package.json/preload.js only):** `cd ~/Documents/Amadeus && npm run build`
- `amadeus.html` and `kurisu_fish_server.py` → NO rebuild, just relaunch

## Voice / memory measurement toolchain (built Sep 3, 2026 — bugs.md 77/78, backlog #176)
All pure-CPU unless noted. **Anything that calls gemma4 must not run while the app is open**
(CLAUDE.md 37) — the probe does, the rest do not.
- `python3 dev/canon_likeness.py --validate` — **run this FIRST.** Self-validates the scorer and
  prints the **noise floor**: at n=30 a real canon subsample scores W≈5.0 words against canon, so
  **a difference under ~5 words at n=30 is not a difference.** `--score FILE` / `--compare A B`.
- `python3 dev/canon_gap_probe.py --n 30 --probes daily|tsundere|tsundere_holdout [--arm X] [--prompt-rev REV] [--seed-base N]`
  — generates replies from the byte-exact `SYSTEM_PROMPT` + live RAG. **Calls gemma4 once per
  reply.** `--prompt-rev` reads the prompt from a git revision, so a BEFORE arm is the real
  shipped prompt, not a hand-revert. Write arms to `dev/canon_arms/`, never a temp dir.
  **Hardened 2026-09-12 (bugs.md 85):** it STOPS if RAG is requested but down (it used to fall
  back silently), refuses to run with the app open, and refuses an `--arm` that adds any
  `prompt_lint` finding over its base prompt (`--allow-lint-delta` to override, and say why).
  Every row records `rag_block`, `arm`, `seed`, `probe_set`, Ollama version and model digest.
  **Same `--seed-base` for two arms = a PAIRED comparison** (verified: same seed → identical reply).
  `tsundere_holdout` was written before any arm saw it — use it to CONFIRM, never to design.
- `python3 dev/opener_family.py FILE.json [--compare BASE ARM] [--canon] [--selftest]` — how she
  STARTS a reply, counted by FAMILY (`W-what`/`Wh-what` → `what`). Also crutch-AGNOSTIC measures
  with canon n=30 p95 beside them (top first word [5], ≤4-word question opener [6], most widespread
  3-gram [3] / 4-gram [2]), echo-question, family-aware stammer rate, tag × opener, Wilson CI.
  Pure CPU. Feed it the `.json` — the `.txt` has no probes, so echo-question cannot be scored.
- `dev/opener_arm.py` — backlog #180 arms (B/C/D/E/F/G/FG) as in-memory transforms. An arm that
  changes the output FORMAT (G: tag at the end) also carries a `history_fn`, so the history she
  reads does not contradict the prompt.
- **Probe history (2026-09-13):** `--history app` is now the DEFAULT — a real greeting from
  `GREETINGS` in the app's `[EMOTION:x] text` form (`amadeus.html:986`). The old fixed `"hey"` +
  bare-tag line is `--history fixed`; runs before 2026-09-13 used it. `--multiturn K` runs K
  conversations of 8 turns (daily / held-out flirty) with her replies fed back as `sendMsg`
  pushes them. `--probes academic` = 30 science/philosophy questions (the longest replies).
- `python3 dev/blind_ab.py make BASE.json CAND.json --out PATH` / `score PATH ANSWERS.txt` — a blind
  paired A/B sheet for Zani: tags stripped, sides randomised, 5 flipped repeats to measure his
  consistency (an always-"A" rater scores 0/5). No model call.
- `dev/canon_arms/PREREG_180.md` — #180's bars, seeds and decision tree, committed before the runs.
  `python3 dev/opener_stage_table.py STAGE HEAD.json NAME=arm:FILE.json ...` scores a stage against it.
  `PREREG_180b.md` is the second screen (arms H, K, HK) after the first stopped at Stage 2.
  `PREREG_180d.md` is the CURRENT goal (Zani's direction: variety + heat by kind of message), scored by
  `python3 dev/opener_heat_table.py HEAD.json NAME=arm:FILE.json` and `--guard daily.json sad.json`.
  Probe sets `holdout2` (23 tease + 22 sincere) and `sad` (30); rows record `probe_kind`.
  `PREREG_180e.md` adds consent-framing arms (Q0/QX/QPX) after 180d showed gemma4 calls him a name 0/17.
  `PREREG_180f.md`: arms T/TQ place EXAMPLE CONVERSATIONS between the system prompt and the history
  (`opener_arm.EXAMPLE_TURNS`, probe `prefix_fn`). **If they ever ship, they must never enter
  `history`** — the diary and fact extractor read it.
- **`canon_gap_probe --relationship-stage N` (2026-09-13):** inserts the app's RELATIONSHIP block
  (parsed from `amadeus.html`) before TWO MODES, as buildSystemPrompt does. Runs before this date
  had NO relationship block. Zani was at stage 3 (score 53.65) on 2026-09-13; stage 0 says "No
  teasing". Any tone/persona arm should run at his real stage.
- `python3 dev/blind_rate.py make A.json B.json --out PATH` / `score PATH VERDICTS.txt` — a BLIND
  deflection read: replies from two runs mixed, tags stripped, sources hidden. Generate the runs
  with `canon_gap_probe --quiet`, or the progress lines un-blind the rater.
- The probe's lint gate compares findings by identity AND count (bugs.md 88): a finding HEAD
  already had is not new, but the same finding on MORE exemplars is.
- `python3 dev/prompt_lint.py [--arm X]` — flags phrases the prompt quotes that appear 0× in canon (split by
  quoted-to-SAY vs quoted-to-FORBID) and exemplar openers over-supplied vs canon. **Run before
  every prompt edit** — it catches the CLAUDE.md 43/45 class mechanically. Not wired into
  `npm run check` (that would need a mutant in `check.selftest.js` in the same commit).
  `--arm X` lints the prompt after an arm; `canon_gap_probe` now does this delta automatically.
- ⚠️ `canon_likeness.py`'s quality guard has two known blind spots (backlog #199): `STAMMER_RE`
  misses `Wh-what`, and `DEFLECT_MARKERS` contains "don't get"/"don't be", so any fix that removes
  "Don't" lowers the deflection rate by construction. Read deflections by eye for #180 work.
- `python3 dev/dedupe_diary.py [--prune FILE] [--apply]` — ChromaDB diary maintenance. **Dry run by
  default**, backs up `chroma.sqlite3` and refuses to proceed without a verified backup.
  **App must be CLOSED** (write lock).
- `dev/stammer_arm.py` — the bugs.md 77 prompt edit as a reviewable transform.
- `python3 dev/translate_probe.py --n 30 [--arm X] [--model M] [--engine deepl] [--kv]` —
  decomposes the TTS translate call into load / prefill / decode using Ollama's own counters.
  **Calls gemma4; spends NO Fish credit** (it never touches `/speak`). Refuses to run with the
  app open, and `verify_shipped_config()` fails loudly if `translate_via_gemma()` drifts from
  what the probe measures. Arms land in `dev/translate_arms/`.
- `python3 dev/translate_register.py ARM_A.json ARM_B.json` — scores Japanese register on two
  arms (feminine/masculine endings, polite です/ます, 私, 君 vs あんた, ザンニー, 紅莉栖, stammer)
  and prints the lines side by side. **The markers are proxies; only Zani can judge the sound.**
  Pure CPU, no model call.

## Presence latency trace (P1, built Sep 4, 2026 — backlog #186)
Measures the ONE number that presence means: **he stops talking → she starts talking**, plus the
per-stage breakdown. Pure instrumentation — no model call, no GPU work, no behaviour change.
- **In DevTools:** `latencyStatus()` — medians/min/max per stage (`latencyStatus('voice')` filters
  by kind). `latencyDump()` → `~/Downloads/amadeus_perf.json`. `latencyReset()` clears the ring,
  so a BEFORE and an AFTER arm are never mixed in one median.
- One `[Perf]` console line prints per turn, so the numbers are visible during normal use.
- **Kill switch:** `PERF_TRACE=false` near the top of the P1 block in `amadeus.html`, then
  relaunch. Everything becomes a no-op and nothing is stored. No code revert needed.
- Storage: `amadeus_perf_v1` in localStorage, ring of 200 turns ≈ 50KB (258 bytes/row, measured).
- **Tests:** `node dev/hf_boot_test.js` (17 checks) covers bugs.md 83 (hands-free idle vs absolute
  timeout) and 84 (the boot prewarm abort). Like the perf test it extracts the shipped blocks from
  `amadeus.html` **by anchor**, so renaming `hfArmIdle` or the boot `Promise.race` fails loudly
  instead of testing a stale copy.
- **Tests:** `node dev/perf_trace_test.js` (45 checks). It extracts the shipped block out of
  `amadeus.html` by anchor — if you rename the `P1: PRESENCE LATENCY TRACE` header or the
  `window.latencyReset=` line, the test fails loudly rather than testing a stale copy.
- **The ring PERSISTS across relaunches** (`amadeus_perf_v1` is read back at load), so n
  accumulates over days. Only `latencyReset()` clears it — nothing else in `amadeus.html`
  removes a localStorage key. Covered by tests 13/14, including corrupt storage.
- `python3 dev/latency_probe.py --n 30 [--no-tts]` — the same pipeline measured OUTSIDE the app
  (live RAG → gemma4 → /speak), so n can be reached without talking to her. **Writes nothing to
  her diary, facts or relationship**, and proves it with Chroma row counts + a sqlite hash taken
  before any import. Refuses to run while the app is open. **It runs on an IDLE machine and reads
  prefill ~1.6x faster than the live app** — use it for A/B and proportions, never for an
  absolute claim (backlog #192/#193).
- **n>=30 before reading any median.** Four turns gave a median that could move ~1s by chance;
  at n=30 that band narrows to ~150ms (bootstrapped on real data, 2026-09-06).

## Stack
- Electron 35 (arm64) → `http://localhost:8765/amadeus.html`
- Ollama gemma4:latest (127.0.0.1:11434, streaming, temp 0.85, num_predict 120, num_ctx 8192, think:false)
- Fish Audio S2 Pro TTS via Flask port 5002 (`kurisu_fish_server.py`)
- RAG server Flask port 5003 (`kurisu_rag_server.py`) — spawned by main.js
- Translator: **gemma4 is primary** (`TRANSLATOR='gemma4'` in kurisu_fish_server.py) — register-aware EN→JP via `translate_via_gemma()`. DeepL is FALLBACK only (header: `Authorization: DeepL-Auth-Key ...`). Set `TRANSLATOR='deepl'` to revert.
- Whisper STT via Flask port 5004 (`kurisu_whisper_server.py`) — `mlx-community/whisper-large-v3-turbo`; returns `no_speech_prob`/`avg_logprob`/`compression_ratio` (max per segment) for the hands-free gate, which also drops a 2–6 word group repeated 4+ times (bugs.md 97)
- Voice model reference_id: `c4d832799bf845ee86638a1bc0cd0d41`
- bge-m3 (Ollama) — RAG embedding, 1024-dim multilingual
- Silero VAD v5 (vendored vendor/vad/, lazy-loaded) — hands-free voice sessions; RMS fallback in amadeus.html

## Files that need rebuild
- `main.js`, `preload.js`, `package.json` → `npm run build`; everything else → relaunch

## Context
- Read ALL files in docs/ at session start
- Obsidian vault at `docs/` — six files, this is the complete list: REFERENCE.md, session-log.md, bugs.md, roadmap.md, kurisu-personality.md, improvements-backlog.md
- The three planning docs (`roadmap-rag-vn.md`, `roadmap-obsidian-mcp.md`, `roadmap-lip-sync.md`) were DELETED on purpose — those features shipped and are documented in roadmap.md / bugs.md / session-log.md. Do not recreate them; older session-log entries still cite them as history.

## BUGS — DO NOT REINTRODUCE
1. Ollama CORS: use `127.0.0.1` NOT `localhost`
2. char_timings null: only check `data.audio_b64`, NEVER require `data.char_timings`
3. Duplicate `const` in sendMsg() crashes all JS → boot video stuck
4. Kurisu name: always クリス (katakana), never 紅莉栖
5. parsEmo(): uses `validEmotions` Set + regex. Strips all `[tags]`, only adopts known emotions.
6. Subtitle sync: word-by-word timed via loadedmetadata. Must NOT dump all at once.
7. playSyncedAudio signature: `(text, audioBase64, emotion)` — text FIRST
8. parsEmo returns `{emotion, text}` — use `parsed.emotion` and `parsed.text`
9. isLoading: reset in `finally` block, not just on success
10. DeepL auth: header `Authorization: DeepL-Auth-Key ...` (NOT form body)
11. Breath sounds: [exhale] only for HIGH_AROUSAL emotions
12. gemma4 thinking tokens: strip `<|channel>thought...<channel|>` from streamedRaw before parsEmo
13. think:false: must be in every Ollama API call
14. EMOTION_OPENER: do NOT prepend separately — Fish Audio vocalises English openers
15. Fish Audio tag grammar: fragment grammar only (noun/adj fragments), no gerund-start/verb-particle clauses
16. Zani pronouns: he/him in SYSTEM_PROMPT. Kurisu self-references about original Kurisu stay she/her.
17. Phase 3 close handlers: BOTH `mainWindow.on('close')` AND `app.on('before-quit')` must check `(diaryHandled && !diaryInProgress)`
18. Phase 3 timeout: `runDiaryWithExit` MUST force-clear `diaryInProgress=false` after race, before `app.quit()`
19. Hardcoded paths: `PYTHON='/opt/homebrew/bin/python3'`, `OLLAMA='/usr/local/bin/ollama'`
20. Textarea Enter: check `e.isComposing||e.keyCode===229` first; use `clearMsgInput()` double-clear pattern
21. Cubism 5: `core.getParameterId(i)` doesn't exist. Scan `core._model.parameters.ids` → `core._parameterIds` → Cubism 4 fallback
22. Lip sync: idle motion overwrites ticker writes. Use `live2dModel.internalModel.on('beforeModelUpdate', ...)`
23. `internalModel.lipSyncValue` doesn't exist. Use beforeModelUpdate hook (bug 22)
24. Web Audio arrays: `getFloatTimeDomainData` → `Float32Array(256)`, `getFloatFrequencyData` → `Float32Array(128)`
25. Lip sync curve: no `pow(x, exp<1)`. Use linear `min(1, smooth × gain)`
26. Lip sync mouth-close: explicit `'ended'`/`'pause'` listeners + silence-aware decay (`peak < threshold` → SILENCE_DECAY)
27. NEVER `process.exit(0)` in close handlers — orphans audio service child → CoreAudio locked → AUDIO_RENDERER_ERROR next launch. Use natural `app.quit()` + `will-quit` 5s unref'd safety valve only.
28. Boot video `preload="none"` — `preload="auto"` + `vid.load()` creates double-load race; `loadeddata` fires for aborted preload, video never plays.
29. Protocol handler MUST use `net.fetch(pathToFileURL(...))` — `new Response(buffer)` has no `Accept-Ranges` support; HTML5 `<video>` needs range requests for progressive load.
30. ~~`playBootVideo()` must NOT have `error` listener during playback wait~~ — **SUPERSEDED by rule 38.** Premise (transient AUDIO events firing `error` on the video element) was voided when the video became permanently muted; an `error` listener is now CORRECT there. See bugs.md 41/43/59.
31. `beforeunload`: explicitly pause/clear all `<audio>`/`<video>` src + `audioCtx.close()` so renderer releases CoreAudio before Electron child shutdown.
32. Fish Audio EMOTION_TAG fragments: every comma-fragment MUST end in an acoustic anchor noun (`quality`, `brightness`, `edge`, `lift`, `pace`, `intensity`, `texture`, `delivery`, `voice`, `pitch`, `form`, `weight`). Fragments ending in adverbs (`throughout`, `always`) or describing pure internal states with no acoustic referent will be vocalised as English speech. Extends bug 15.
33. `prewarmOllama()` MUST include `num_ctx:8192` — matches `sendMsg()`. Without it, Ollama allocates a different KV buffer size and the prewarm cache is discarded on first real message.
34. `prewarmOllamaMain()` in main.js MUST be aborted (AbortController) before `createWindow()` opens — a stale bare-`'hi'` request arriving after the renderer's system-prompt prewarm evicts the KV cache.
35. Boot video src: assigning `vid.src` ITSELF invokes the media load algorithm — NEVER follow a src assignment with `vid.load()` (double-invocation = bug 28's race in disguise: intermittent never-plays / mid-play stops). Each load attempt = exactly ONE invocation — src swap OR load(), never both, listeners attached first. (Recorded as bug 58 in docs/bugs.md.)
36. Boot video must decode on an IDLE system — never let `prewarmOllama()`, greeting synthesis, or any gemma4/heavy IPC work run CONCURRENTLY with playback. Fire-and-forget before `playBootVideo()` is the trap (it keeps running during the video). Measured: it starves the decoder and stalls playback mid-video (bug 60). Current design (bug 63, CORRECTED 2026-09-07 — bugs.md 84): the prewarm runs BEFORE the video, capped by `await Promise.race([prewarmOllama(pwAbort.signal), delay(4000)])` and then **explicitly aborted** — `Promise.race` does NOT cancel the loser, so until this was fixed a slow prewarm kept running through playback (bug 60, reintroduced by a comment that had stopped being true). **The abort bounds the overlap at ~1.7s, not zero:** measured 2026-09-07, an abandoned prefill leaves Ollama busy a further 1.72s. Do not claim "nothing overlaps" — and greeting audio is only prefetched when already cached (a miss defers synthesis past the reveal). Prewarm must never be fire-and-forget near the video, and must never sit next to `initLive2D()` either (bug 62: it stutters her entrance).
37. gemma4 runs 100% on GPU — the SAME GPU as Kurisu's WebGL/Live2D rendering. Every inference costs ~0.66s of animation-stuttering GPU saturation AND evicts the chat KV prefix. So ANY background gemma4 caller (greeting warmer, facts extraction, study watcher, proactive nudge) MUST be (a) idle-gated — never fire while Zani may be interacting — and (b) abortable via `noteActivity()`. Measured regression: bug 61.
    **(a) and (b) are DIFFERENT properties and both are required.** A gate decides when work
    STARTS; only a brake can end it. `extractFactsNow` was gated but not abortable and held
    the GPU up to 9.66s (bugs.md 74). Abortable means the GPU is actually released, not just
    the client — verify with a probe call straight after the abort. If an abort would discard
    work worth keeping, RE-QUEUE it (bugs.md 74 re-arms the extraction) rather than losing it.
    **Any change that makes a background call LONGER must be re-checked against this rule**,
    not only against rule 40 — that is exactly how bugs.md 73's cap raise created bugs.md 74.
    Still non-compliant: `studyTick` (backlog #173).
38. Boot video element is PERMANENTLY MUTED (`vid.muted=true`, soundtrack on a separate `<audio>`). This makes the VISUAL structurally immune to the whole CoreAudio/audio-renderer failure class — a broken audio stack yields a silent boot video, never a frozen one. Because of this an `error` listener in the playback wait is now correct and required (it means a real visual failure). Do NOT unmute the video element to "restore boot sound" — that reintroduces bugs 41/43/55/59. (bugs.md 59)
39. Lip-sync `createMediaElementSource` MUST be disconnected when its `<audio>` is abandoned (`teardownLipSource()` in `onAudioStop`, idempotent) — otherwise nodes accumulate on the analyser for the whole session. But NEVER disconnect an element that could play again: her voice routes THROUGH that node, so a live disconnect = silence. Safe today only because nothing resumes a reply element. (bugs.md 66)
40. `num_predict` truncation: ANY Ollama call whose output is spoken, pushed to `history`,
    **or injected back into her prompt** must be trimmed to the last complete sentence —
    otherwise a mid-sentence fragment becomes permanent memory via the diary and fact
    extractor. `ollamaStream` reports it via the optional `meta` out-param. (bugs.md 67)
    **The injected case is the worst of the three** (bugs.md 70): a truncated reply costs
    one turn, but a truncated *memory* sits in EVERY prompt until it is regenerated. The
    stage-2 summary ran unguarded at `num_predict:100` and was a fragment 63% of the time.
    Trim unconditionally rather than gating on `done_reason` — trimming well-formed text is
    a no-op, and the field has already changed shape between Ollama versions. For a memory
    write, prefer storing NOTHING over storing a fragment: keep the previous good value and
    retry. Do not blindly reuse `trimToLastSentence` for this — its bail-out is tuned for
    already-SPOKEN replies and inverts the trade-off.
    **Size `num_predict` against what the prompt ASKS FOR, and state the headroom ratio.**
    Risk is the ask/cap ratio, not the cap's absolute size. Measured: "3-4 sentences" at 100
    (~0.8x) truncated 63% (bugs.md 70); an unbounded JSON list at 300 (~0.8x) truncated 33%
    (bugs.md 73); "one short line" at 80 (~4x) truncated 0/90 (backlog #159). And in JSON
    mode a truncation is UNPARSEABLE, so the whole result is discarded — fail-closed, but
    silent without telemetry.
41. RAG/per-turn context must NEVER live inside the system message. Anything that changes
    each turn placed there sits AHEAD of all history, so the shared prefix ends there and
    the whole conversation re-prefills every turn. Measured: 672ms → 176ms per turn by
    moving it to its own system message before the user turn. Same rule for any future
    per-turn injection (memory-panel note already moved). (bugs.md 68)
42. Anything injected into her prompt AS HER OWN WORDS must be generated in her SPOKEN
    register. This bit TWICE — the diary (bugs.md 69) and then the stage-2 summary
    (bugs.md 71, measured 97% case-file register). When you add ANY new generator whose
    output re-enters her prompt, the vocabulary constraint is part of shipping it, not a
    follow-up. And measure the CONTENT too: a variant that scored a perfect 0% register
    was rejected for halving what she actually remembered. The diary had no vocabulary constraint while her speech had a full banned
    list, so entries came out in lab prose and she quoted them back verbatim (*"your
    'biological hardware'"*). Measured: clinical memory → 14% clinical replies, plain
    memory → 0%, p=0.027. Applies to any future memory/summary/fact text too. (bugs.md 69)

43. NEVER quote a phrase in SYSTEM_PROMPT that you don't want her to say — not even to
    FORBID it. Naming it supplies it as an exemplar. "Don't get the wrong idea" was quoted
    twice (as a tsundere example, and as a crutch to avoid) and appeared in 37% of replies,
    while the real Kurisu VN corpus never says it at all. Describe the BEHAVIOUR instead.
    **And it must be absent everywhere:** fixing one of the two sites changed nothing
    (p=0.70 and p=0.50); removing both took it to 3%. One mention anywhere is enough to keep
    the phrase alive, so an A/B that changes a single site will wrongly read as "no effect".
    Same family as backlog #163. (bugs.md 76)
44. Any Ollama model the app depends on INTERACTIVELY must pass its own `keep_alive`.
    **Never rely on Ollama's default — it is not a stable contract.** On 0.32.15 the default
    was 5 minutes; on **0.33.2 it is 30 minutes** (measured 2026-08-31: an embed sent with no
    `keep_alive` came back with `expires_at` 30.0 min away). **The machine now runs 0.34.4
    (`/api/version`, 2026-09-27 — it upgraded itself again).** Its `server config` log line reads
    `OLLAMA_KEEP_ALIVE:5m0s` (all six retained `server*.log`, 2026-09-23 → 09-27) — the default looks
    like **5 minutes again**. Not yet cross-checked with `/api/ps` `expires_at`; do that before citing it. The default changed under us
    within a week, which is the argument FOR this rule, not against it: bugs.md 75's fix is
    now belt-and-braces on this version and load-bearing again the moment the default moves
    back. State the TTL explicitly and never infer it. The history below is why:
    Every gemma4 call passes `'30m'`; the bge-m3 embeddings in
    `kurisu_rag_server.py` passed nothing, so the RAG server's startup warm-up expired 5
    minutes after launch and the first message of a session paid an **812ms** cold model load
    (vs 10ms warm) on the GPU that renders her. A default TTL shorter than the user's natural
    think-time turns a warm-up into a wasted one. Check with `/api/ps` `expires_at`. (bugs.md 75)

45. **A mandatory instruction PLUS a list of exemplars produces the first list item, at a rate
    a mere quotation never reaches.** `ROMANTIC/FEELINGS` said *Begin with a stammer: "W-what—",
    "I-I wasn't—", "Th-that's not—"* — she opened **83%** of flirty replies with the first one, on
    3 distinct openers in 30. Compare bugs.md 76, where a phrase merely *quoted* twice reached 37%.
    Compulsory + enumerated is roughly twice as strong as quoted.
    **The fix is not a longer list or a "vary it" plea — replace the LIST with a RULE for FORMING
    the thing.** *"Build the stammer out of the word you were ALREADY going to say"* generates a
    different result per sentence and supplies no phrase, so rule 43 cannot be violated by
    construction. Measured 83% → 37%, p=0.00048, with deflection and tag rates intact (bugs.md 77).
    **Derive the target rate from the corpus, never from taste:** canon stammers on 3% of lines and
    42 of its 48 stammers are distinct — the prompt was wrong on RATE and on VARIETY, and only the
    corpus could say so. And **check your own replacements against rule 43 before shipping**: two of
    mine both opened on "Don't" and it went 13% → 33% — the same mistake, one iteration later
    (backlog #180).
46. **A rate quoted for a GROUP of phrases says nothing about any one member.** bugs.md 76's
    *"hmph / it's not like / w-what stay ~90-100%"* was read as a rate for "Hmph"; "Hmph" is
    actually ~1.7%, and the group figure was carried entirely by "W-what" at 83%. That misreading
    became backlog #177 and nearly bought a fix for a non-problem. **Re-measure the individual
    phrase before spending a session on it** — it costs ~60s with `dev/canon_gap_probe.py`.
47. **Canned strings pushed into `history` are in-context exemplars, not just displayed text.**
    Three sites push the chosen greeting into `history` as an assistant turn, and one pushes the
    birthday gift line — so hand-written content sits in the conversation as her own prior words
    for the rest of the session, a stronger position than a prompt exemplar. When auditing the
    prompt for a phrase, audit these too (backlog #179).
    **Grep for them, do not trust a line number here:**
    `grep -n "history.push({role:'assistant'" amadeus.html`. The numbers in this rule were wrong
    within two sessions of being written (`:4904` pointed at a `catch` block), because every
    edit above them shifts them. Cite the grep, not the line.
48. **Instrumentation must be TOTAL, and every clock it starts must be closed or aborted.**
    Two separate traps, both found while building the P1 latency trace (backlog #186):
    **(a) It must never throw into its caller.** `ttsSpeak` is deliberately not awaited by
    `sendMsg` precisely so its failures cannot reach `sendMsg`'s catch — which runs
    `history.pop()` and would corrupt the conversation. A measurement helper that throws
    (a full `localStorage`, a missing field) re-creates that bug from a new direction. Every
    helper catches its own errors and returns undefined.
    **(b) A leaked start-time is INVISIBLE and it corrupts the next measurement, not this one.**
    A voice utterance opens a timer at speech end, then can die at four places that never reach
    a reply: the Whisper no-speech gate, a VAD misfire, `sendMsg`'s `isLoading` early return, and
    the diary-overlay early return. Any one of them leaves the clock running, and the NEXT turn
    reports a wait that never happened. Nothing on screen shows it. **Enumerate every exit path
    before shipping a timer, and unit-test the abort** — `node dev/perf_trace_test.js` extracts
    the shipped block out of `amadeus.html` by anchor and drives those paths.
    **(c) Enumerate every ENTRY path too, not just the exits.** bugs.md 80: the mic button runs
    TWO different code paths depending on `voiceFirstOn` — Hands-Free ON starts the Silero
    session, OFF runs the original tap-to-record. P1 instrumented the first and never asked
    whether another way in existed. **The uninstrumented one was the DEFAULT**, so Zani's first
    real voice session recorded every spoken turn as `kind:'text'` and `latencyStatus('voice')`
    said "no turns recorded yet" after a genuine conversation.
    **(d) A filter that hides data is indistinguishable from data loss.** The same bug had a
    second half: `latencyStatus(kind)` matched by exact equality, so `'voice-rms'` and
    `'voice-tap'` rows were invisible to `latencyStatus('voice')`. Prefix-match anything that
    groups a family of kinds, and test the grouping.

49. **`npm run check` PARSES; it does not resolve names. A deleted `const` is invisible to it.**
    Removing two `...` writes from `sendMsg` also removed the `const subEn` / `const subEl`
    they declared — and a later line still used both. That is a `ReferenceError` inside the
    `try` on EVERY turn, which the catch converts into a popped history entry and an error
    subtitle. **The gate went green.** (bugs.md 81)
    **After any edit that DELETES a declaration, audit the enclosing function's identifiers**,
    not just the lines you touched. The one-liner that catches it:
    extract the function body, collect every `const|let|var` name (**splitting on commas** —
    `const a=…, b=…` declares two), and diff against every identifier used. A naive regex that
    misses the comma form produces false positives; mine did, and I nearly chased one.
    The gate cannot grow teeth here cheaply — a real linter is backlog work — so this is a
    discipline, not a check.

50. **Test the OUTCOME the user needs, not the mechanism you built.** bugs.md 82: P4 shipped with
    `npm run check` green, 22 unit tests green, and two mutants correctly caught — and it made her
    reply text invisible on every normal turn. Every test asked "does my indicator behave?"; none
    asked **"after a normal reply, are her words on screen?"**
    **Corollary — writing to an element and MAKING IT VISIBLE are different responsibilities.**
    I audited all nine writers of `#sub-en` (who puts text in) and never audited who sets `.on`
    on `#subtitle` (who makes it display). `playSyncedAudio` does the first and not the second;
    it depends on `sendMsg` for visibility. **When you touch a display path, grep the class that
    controls `display`, not just the property that holds the content.**
    Third instance of this error: backlog #170 (a gate that did not read the changed file),
    bugs.md 80 (one entry path traced, assumed to be the only one), bugs.md 82 (mechanism tested,
    outcome not).

51. **The display layer is FROZEN by Zani (2026-09-07). Do not touch it without asking.**
    Subtitle reveal, its audio-timed word sync, the `...` placeholder, the thinking dots, and the
    order in which text and voice arrive are all settled. Two attempts to improve them were
    rejected in one session — one on taste (streaming text spoils the line before she says it)
    and one on both taste and a regression (bugs.md 81/82).
    **Reducing her response TIME is still wanted, as long as quality holds.** The distinction is
    the point: change what happens BEFORE the words reach the screen, never how they reach it.

52. **A measurement tool must FAIL when its condition is not met — never fall back quietly.**
    `canon_gap_probe` returned "nothing retrieved" when the RAG server was down, printed "live
    server on 5003", and a no-RAG run was committed as the #180 baseline (bugs.md 85). Any probe
    field that says what condition ran (`rag_used`, `arm`, `seed`) is worthless if nobody checks
    it — **make the tool check it and stop.** Same family as bugs.md 80 (a missing entry path
    logged as "text") and rule 48(d) (a filter that hides data looks like data loss).
    **The same applies to a CACHE with a working fallback:** the greeting cache missed 100% of the time
    for ten weeks and she still spoke, just late (bugs.md 91). When a read misses, compare the READ path
    with the WRITE path; and to tell a new file from a rewritten one, read its creation time, not mtime.
    **And for a memory WRITER:** the facts store stayed empty for ten weeks and nobody could say whether the
    extractor failed, never ran, or found nothing (bugs.md 92). Record every run; give it a guaranteed trigger.
    **And every spawn must say where its output goes:** a default `'pipe'` nobody reads loses the output AND
    blocks the child once ~131 KB is written (bugs.md 93). Use `spawnLogged`; never fall back to `'pipe'`.

53. **For a TONE or VOICE change, offline metrics can only REJECT a candidate — never approve one.**
    #180's Q0 passed every pre-registered guard (opener variety, repeated phrases, length, names in
    daily/sad chat, tag rates), shipped, and Zani reverted it three days later: *"way too calm"*,
    *"I like her voice before"*. The measures count SHAPE — first words, repeated n-grams, tags — and
    nothing counts felt sharpness; the probe also has no facts, diary or memory blocks. **Plan the live
    trial as part of the work, not as an afterthought:** one commit, byte-identical to the arm you
    measured, a `pre-<name>` tag first, and a one-command revert written down before he starts. And
    when he reports a feel, believe the report over the table (bugs.md 90).

## Key Architecture
- **UI palette:** red — `--bg:#060404`, `--blue:#c0392b`, `--blue-bright:#e84040`. Background = CSS grid via `#app::before`.
- **Subtitle sync:** msPerWord = (audioDuration × 0.95 × 1000) / wordCount via loadedmetadata; 300ms fallback
- **Emotion** set at moment playSyncedAudio starts
- **Ollama:** only start if not running, keep_alive:'30m', think:false always
- **Fish Audio:** temp 0.7, top_p 0.8, repetition_penalty 1.2, normalize True, speed FIXED 1.1, NO inline prosody tags — "V3" config from July 13 2026 voice A/B test (dev/voice_ab_test.py). Bump GREETING_TTS_VER in amadeus.html if these change.
- **Lip sync calibration** (near top of amadeus.html): AMPLITUDE_GAIN=3, ATTACK_FACTOR=0.8, DECAY_FACTOR=0.18, SILENCE_DECAY=0.55, SILENCE_THRESHOLD=0.012, MOUTH_FADE_MS=100, VOWEL_FORM_SCALE=0.7, VOWEL_RATIO_CENTER=0.25, VOWEL_RATIO_GAIN=3.5, IDLE_FORM=-0.49
- **HISTORY_WINDOW=30** — max messages sent to Ollama per turn (15 exchanges). Full history array kept for diary generation.

## RAG (Phase 1)
- FOUR ChromaDB collections at `~/Documents/Amadeus/data/chroma/`: `kurisu_ja` (756 clips) + `kurisu_en` (1672 lines) + `amadeus_diary` (56 rows as of 2026-09-03) + `amadeus_behavior` (15 situational rules, indexed at startup)
- **`amadeus_diary` row ids are `'d' + sha1(text)[:16]` (bugs.md 78).** They were the entry's DATE, or its ARRAY POSITION when dates collided — and entries are `unshift()`ed, so positions shift on every write and `upsert` created a new row each launch. That left 79 rows for 55 entries, one stored 5×, **weighting retrieval by duplication rather than relevance.** `/index-diary` skips by TEXT, not id, so it is correct whether or not `dev/dedupe_diary.py` has run, and a normal launch embeds only what is NEW — usually **1** entry, the previous session's (bugs.md 95: the close no longer indexes; the boot index reconciles) — instead of all 50 (it is fire-and-forget during boot — CLAUDE.md 36/37).
- **Invariant (bugs.md 95): every localStorage diary entry is in `amadeus_diary`.** Check it with
  `python3 dev/diary_index_check.py` (app CLOSED; read-only, works on copies; exit 0 = none missing, 3 = missing,
  1 = could not read — it never reports 0 for data it did not decode). Right after a close, 1 missing is EXPECTED.
- **The collection is deliberately a SUPERSET of the 50-entry localStorage diary** — it retains entries that aged out. Never "mirror localStorage"; that destroys real long-term memory.
- Server: port 5003, k=3 per collection, 4s timeout, falls through on failure. Renderer has a 60s circuit breaker (`_ragDownUntil`) so a dead server costs 4s ONCE per minute, not per message.
- HYBRID retrieval: dense (bge-m3) + Okapi BM25 lexical (EN words / JA char-bigrams, zero deps) fused by reciprocal-rank fusion. Gates: `STYLE_THRESHOLD=0.7` (en/ja), `BEHAVIOR_THRESHOLD=0.5`. Per-query distances logged to `data/rag_trace.log` for tuning.
- Injection (CHANGED Aug 18, 2026 — bugs.md 68): `sendMsg` no longer passes ragCtx into
  `buildSystemPrompt`. The retrieved block is its own `system` message spliced in just
  BEFORE the current user turn (`RAG_AS_TAIL_MESSAGE=true`), so the system message stays
  byte-identical all session and the KV prefix survives. Order within the block is
  unchanged: EN ("STYLE EXAMPLES") then JA ("VOICE ANCHORS") then diary then behavior.
  `buildSystemPrompt(ragContext)` still supports the old layout for the flag-off path.
- JA block must say "do NOT translate, do NOT quote, do NOT respond in Japanese"
- Only `sendMsg()` passes ragCtx; ttsGreeting/generateDiaryEntry use bare SYSTEM_PROMPT

## Session Memory
- Sliding window of 7 diary entries injected at `\nCHARACTER\n` anchor in SYSTEM_PROMPT
- Time context appended at END for recency bias. `formatTimeContext()` ALWAYS states today's date + weekday (bug 64 — without a clock she cannot tell a dated fact has passed); the 01:00-04:59 sleep nudge is an ADDITION to that, not the whole thing
- Diary auto-saves on close via `runDiaryOnClose`/`runDiaryWithExit`; "SAVING SESSION" overlay shown
- Stage-2 rollup (`main.js`): `num_predict:180` (NOT 100 — at 100 it truncated 63% of the
  time) and guarded by `trimSummaryToLastSentence()`, which returns `null` rather than store
  a fragment; `null` keeps the previous summary and retries next close (bugs.md 70).
  Unit tests: `node dev/trim_summary_test.js`

## LocalStorage keys
- `amadeus_last_seen` — last boot timestamp (absence tier detection: 24h/72h/336h)
- `amadeus_recent_greetings` — `{arrayName:[recentIndices]}` for `pickFresh()` repeat avoidance
- `amadeus_diary_v1` (DIARY_KEY) · `amadeus_diary_summary` + `amadeus_diary_summary_watermark` (stage-2 rollup)
- `amadeus_facts_v1` (FACTS_KEY) — structured fact memory; each `{fact, category, date, event_date, seen?}`.
  `date` = first learned (or replaced); `seen` = renewed (re-stored duplicate or memory-panel edit). Store order is
  most-recently-renewed first, so the 60-cap drops the least recently renewed (backlog #216). **Never written before bugs.md 92 (2026-09-27).**
- `amadeus_facts_runs_v1` — every facts extraction run (ring of 50): trigger `idle`/`close`, outcome, facts returned, `evalCount`, `doneReason`, ms. DevTools: `factsRuns()`.
- `amadeus_relationship` — `{score, sessions, sessionExchanges}`
- `amadeus_perf_v1` — P1 presence latency trace, ring of 200 turns (~50KB). `latencyReset()` clears it.
- `amadeus_dmails_v1` (DMAIL_KEY) · `amadeus_birthday_v1` (BIRTHDAY_KEY) · `amadeus_voice_first` (hands-free toggle)
- `amadeus_diary_bak_<ms>` — full diary snapshot written by `rewriteClinicalDiary({apply:true})`
  before it edits anything. localStorage has no undo; this is the only way back. Never auto-pruned.

## System Prompt (Variant B)
- IDENTITY → USER → ABOUT ZANI → [memory] → CHARACTER → WHAT YOU KNOW → [relationship directive] → TWO MODES (CASUAL incl. word rule + banned list / ACADEMIC) → ENDINGS → EMOTION TAG → INPUT→EMOTION → **OUTPUT→EMOTION** → ROMANTIC/FEELINGS → RULES → **VARIETY RULE** → EXAMPLES (38 lines, 31% of the prompt) → [time context] → [RAG tail message]
- Verified against `amadeus.html:454` on 2026-09-03. OUTPUT→EMOTION and VARIETY RULE were missing from this map before that date.
- Zani: age 18, birthday 11 June, Student, England; interests: rhythm games, anime, football, piano, chess
- CASUAL ≤35 words; ACADEMIC ≤70 words (science only); ROMANTIC → always [flustered]/[tsundere]

## 20 Emotions
happy, excited, sad, angry, scared, surprised, smug, embarrassed, calm, thinking, tsundere, sarcastic, flustered, dismissive, curious, lecture, melancholic, teasing, annoyed, default

## Greetings (14 arrays)
Generic(25), Morning/Afternoon/Evening(8 each), Night(8, 21:00-00:59), SmallHours(4, 01:00-04:59), Kurisu birthday Jul25(4), Zani birthday Jun11(4)+Eve Jun10(3)+After Jun12(3), ShortAway 24-72h(3), MediumAway 3-14d(3), LongAway 14d+(3), IncomingCall(4). Routing: birthdays → absence → time-of-day. All go through `pickFresh()`. Safe emotions only (no melancholic/thinking/embarrassed/flustered).

## IPC channels
preload.js (15): request-conversation, conversation-response, save-diary-entry, diary-save-complete, show-saving-overlay, request-diary-entries, diary-entries-response, save-diary-summary, diary-summary-saved, incoming-call-accepted, window-hidden, window-shown, cache-greeting-audio, **run-facts-extraction, facts-extraction-done** (bugs.md 92).
Close budget (grep the names in main.js — do not trust a line number): `DIARY_TIMEOUT_MS=40000` outer race; `OLLAMA_FETCH_TIMEOUT_MS=12000` and `SUMMARY_FETCH_TIMEOUT_MS=12000` per-call; `FACTS_CLOSE_WAIT_MS=25000` for Step 5, the facts pass, which runs LAST (renderer aborts at 24s).

## MCP Tools
- **obsidian** (`@bitbonsai/mcpvault`) — vault: `/Users/zha61/Documents/Amadeus/docs`
  - append mode for session-log.md and bugs.md; overwrite for full replacements
  - full npx path required: `/opt/homebrew/bin/npx`

## Credentials → see docs/REFERENCE.md
## Full architecture, bugs → see docs/
