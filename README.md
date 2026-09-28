# Amadeus

A local, voice-enabled AI companion for macOS, inspired by the "Amadeus" system in *Steins;Gate 0*.
She talks with a Live2D avatar, speaks in Japanese with timed English subtitles, listens hands-free,
and keeps a long-term memory of past conversations. The language model runs **on-device** (Ollama);
only speech synthesis and an optional translation fallback are cloud APIs.

> Fan project, not affiliated with or endorsed by MAGES./5pb., Chiyomaru Studio or the *Steins;Gate*
> rights holders. **No character assets are included** — no Live2D model, voice recordings, music,
> logo or game script. See [Supplying your own assets](#supplying-your-own-assets).

## What it does
- **Conversation** — `gemma4` via Ollama, streamed, with a character system prompt, a per-turn RAG
  block and a sliding window of recent diary memory.
- **Voice** — replies are translated EN→JA in her register (by the local model, DeepL as fallback)
  and synthesised with Fish Audio; subtitles are revealed word-by-word, timed to the audio length.
- **Hands-free listening** — voice-activity detection (Silero VAD, adaptive-RMS fallback) →
  local Whisper (`mlx-whisper`, large-v3-turbo) with a no-speech gate.
- **Memory** — a diary entry is written at every close; older entries are rolled up into a
  long-term summary; durable facts are extracted to a structured store with temporal labels.
- **Retrieval** — hybrid RAG: dense embeddings (`bge-m3`, ChromaDB) + Okapi BM25, fused with
  reciprocal-rank fusion, with distance gates against content bleed.
- **Presence** — Live2D lip-sync from the audio signal, idle behaviour, greetings by time of day
  and absence, and a proactive nudge after long silence.

## Architecture
```
Electron main (main.js) ── spawns & supervises ──┬─ http.server :8765  (serves amadeus.html)
   │  diary / summary / facts at close           ├─ kurisu_fish_server.py    :5002  translate → Fish TTS
   │  log sink → data/logs/                      ├─ kurisu_rag_server.py     :5003  ChromaDB + BM25
   ▼                                             └─ kurisu_whisper_server.py :5004  mlx-whisper STT
Renderer (amadeus.html) ── streams ──► Ollama :11434 (gemma4, bge-m3)
```

## Engineering notes
The project is run with a measurement-first discipline, and the history is documented in
[`docs/`](docs/) (`bugs.md`, `improvements-backlog.md`, `session-log.md`).
- **Every non-trivial change is measured before it ships**, usually at n=30 with paired seeds and
  pass levels written down *before* the runs (e.g. [`dev/facts_arms/PREREG_216.md`](dev/facts_arms/PREREG_216.md),
  where the candidate failed and was not shipped).
- **KV-cache discipline** — per-turn retrieval lives in its own message after the history, so the
  system prompt stays byte-identical and its prefix is reused (672 ms → 176 ms prefill per turn, bugs.md 68).
- **Silent-fallback audit** — every fallback path was checked for evidence that its primary path
  really runs; it found a greeting cache that had never hit, a fact store that had never been written,
  and child processes whose unread stdout pipes would eventually block them (bugs.md 91–93).
- **Tests check outcomes, not mechanisms**, and extract the shipped code by anchor so they cannot
  silently test a stale copy. Several suites plant mutants to prove they can fail. Run them with
  `node dev/<name>_test.js`; `npm run check` is the pre-launch gate.
- **Resource budget** — built for a 16 GB M5 MacBook Pro; gemma4 is ~4.1 GiB resident.

## Requirements
- macOS on Apple Silicon, Node.js + Electron 35, Python 3 (`/opt/homebrew/bin/python3`)
- [Ollama](https://ollama.com) with `gemma4:latest` and `bge-m3`
- Python packages: `flask flask-cors requests chromadb mlx-whisper`
- A Fish Audio API key and voice model; a DeepL API key (fallback translator)

## Setup
1. Clone to `~/Documents/Amadeus` (the path is currently fixed in `main.js`).
2. Create `config.json` (git-ignored): `{"fish_api_key": "...", "deepl_api_key": "..."}`.
3. `npm install`, then `npm run check`.
4. Supply the assets below, build the RAG index (`python3 build_kurisu_index.py`, which expects your
   own line datasets — see the paths at the top of that file).
5. `npm run build`, then `open dist/mac-arm64/Amadeus.app`.

## Supplying your own assets
Not in this repository (git-ignored); the app expects them at these paths:
| Path | What |
|---|---|
| `live2d/Kurisu/Kurisu.model3.json` (+ textures, motions) | a Live2D Cubism model |
| `assets/icon.icns`, `assets/ama.webp`, `amadeus_logo.png` | app icon and logo |
| `amadeus_startup.mp4`, `music/` | boot video and background music |
| `data/` | runtime data (ChromaDB, caches, logs) — created by the app |
The Fish Audio voice model ID is set in `kurisu_fish_server.py`.

## Status
A personal project, in active use. Built with Claude Code as a pair-programmer.
