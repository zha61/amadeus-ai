#!/usr/bin/env python3
"""
latency_probe.py — measure the presence pipeline WITHOUT talking to her.

WHY THIS EXISTS
    P1 (backlog #186) measures the real app, but it needs Zani to hold ~30 real
    conversations. Driving her chat automatically to get that n is NOT a free
    substitute: every turn in the app is pushed to `history`, rolled into her
    DIARY on close, fed to `maybeExtractFacts()` (which writes
    `amadeus_facts_v1`, injected into every future prompt), and bumps her
    relationship score. Thirty synthetic turns would become thirty false
    memories. Zani asked for the measurement WITHOUT that, and he was right to.

    So this probe runs the same pipeline outside the app:
        live RAG  ->  gemma4 (real SYSTEM_PROMPT, real history)  ->  /speak
    It measures every stage of the wait except STT and ~3ms of playback start.

WHAT IT CANNOT TELL YOU
    * The VOICE path. There is no microphone here, so `stt` is never exercised.
      That still needs a real hands-free session in the app.
    * Renderer-side playback start. P1 measured this live at 3ms, so it is noise.
    * It is a CONTROLLED replay, not organic use: the same base history for every
      call, so prompt size does not drift the way a real conversation's does.

WHAT IT WRITES  (checked, and re-checked at exit)
    * NOTHING to her diary — `/index-diary` is never called, and localStorage is
      unreachable from python. Her diary, facts and relationship are untouched.
    * `amadeus_behavior` gets its 15 static rules re-upserted, because that runs
      at import of kurisu_rag_server — exactly as it does on every normal launch.
      Same content, no change.
    * ~n lines appended to `data/rag_trace.log` (a rotating tuning log).
    * Fish Audio API calls: one short TTS per probe unless --no-tts.
    It snapshots Chroma row counts + the sqlite3 hash before and after, and
    PRINTS THE COMPARISON, so the claim above is evidence rather than a promise.

APP MUST BE CLOSED — it calls gemma4 (CLAUDE.md 37) and opens the Chroma DB.

Usage:
    python3 dev/latency_probe.py --n 30
    python3 dev/latency_probe.py --n 5 --no-tts     # rehearsal, no Fish spend
"""

import argparse
import hashlib
import json
import os
import re
import statistics as st
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

CHROMA_DB = os.path.join(ROOT, 'data', 'chroma', 'chroma.sqlite3')
CAPTURE = os.path.expanduser('~/Downloads/amadeus_turn.json')
OUT_DIR = os.path.join(HERE, 'latency_arms')
OLLAMA_CHAT = 'http://127.0.0.1:11434/api/chat'

import requests  # noqa: E402  (after sys.path setup)

sys.path.insert(0, HERE)
from canon_gap_probe import PROBES, format_retrieved  # noqa: E402


# ── safety ──────────────────────────────────────────────────────────────────
def app_is_running():
    """The app serves amadeus.html on 8765 and spawns the servers. If it is up,
    gemma4 is shared with her Live2D rendering (CLAUDE.md 37) and the timings
    here would be contended nonsense."""
    try:
        requests.get('http://127.0.0.1:8765/amadeus.html', timeout=1)
        return True
    except Exception:
        pass
    try:
        out = subprocess.run(['pgrep', '-f', 'Amadeus.app'], capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def db_hash():
    """Hash of the whole Chroma file. Pure file read — needs NO import, which is
    the point: see the note in memory_snapshot()."""
    try:
        h = hashlib.sha256()
        with open(CHROMA_DB, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception as e:
        return f'unavailable ({e.__class__.__name__})'


def memory_snapshot(rag_mod):
    """Row counts for every collection plus a hash of the whole DB file.

    CAUTION, learned the hard way on 2026-09-06: importing kurisu_rag_server
    RE-UPSERTS the 15 static behavior rules at module level. A 'before' snapshot
    taken after that import cannot see it, so before==after looked like a clean
    proof while the file hash had in fact moved between runs. The real baseline
    hash is taken by db_hash() BEFORE any import — that is the honest one.
    """
    snap = {}
    for name in ('kurisu_ja', 'kurisu_en', 'amadeus_diary', 'amadeus_behavior'):
        try:
            snap[name] = rag_mod._client.get_collection(name).count()
        except Exception as e:
            snap[name] = f'unavailable ({e.__class__.__name__})'
    snap['_sqlite_sha256'] = db_hash()
    return snap


# ── the real prompt ─────────────────────────────────────────────────────────
def load_base_messages(path=CAPTURE):
    """A REAL captured turn, minus its trailing RAG block and user message.

    Using a real capture rather than rebuilding the prompt matters: the memory
    blocks buildSystemPrompt() injects (diary window, facts, relationship
    directive) live in localStorage and cannot be reached from python. Rebuilt,
    the prompt would come out ~1,000 tokens short and prefill would read
    optimistically low.
    """
    if not os.path.exists(path):
        sys.exit(f'No turn capture at {path}.\n'
                 f'Run dumpLastTurn() in the app DevTools first, or pass --capture.')
    data = json.load(open(path))
    turns = data if isinstance(data, list) else [data]
    turns = [t for t in turns if t.get('messages')]
    if not turns:
        sys.exit(f'{path} holds no messages arrays.')
    # The richest capture = the most prompt tokens = closest to steady state.
    t = max(turns, key=lambda x: x.get('promptTokens') or 0)
    msgs = t['messages']
    if not (len(msgs) >= 2 and msgs[-1]['role'] == 'user' and msgs[-2]['role'] == 'system'):
        sys.exit('Unexpected capture shape: expected [... , system(RAG), user].')
    # Images are stored as size markers by recordTurn, never as base64 — but be
    # explicit, because an image would change prefill completely.
    base = [m for m in msgs[:-2]]
    for m in base:
        m.pop('images', None)
    return base, t


EMO_RE = re.compile(r'^\s*\[([a-z_]+)\]\s*', re.I)


def split_emotion(raw):
    m = EMO_RE.match(raw or '')
    return (m.group(1).lower(), raw[m.end():].strip()) if m else ('default', (raw or '').strip())


def one_turn(base, probe, rag_client, fish_client, do_tts):
    row = {'probe': probe}
    t0 = time.perf_counter()

    # 1. RAG — same endpoint and same splice position as sendMsg.
    try:
        r = rag_client.post('/retrieve', json={'query': probe})
        ctx = r.get_json() if r.status_code == 200 else None
    except Exception:
        ctx = None
    row['rag_ms'] = int((time.perf_counter() - t0) * 1000)
    tail = (format_retrieved(ctx) or '').strip()

    msgs = list(base)
    if tail:
        msgs.append({'role': 'system', 'content': tail})
    msgs.append({'role': 'user', 'content': probe})
    row['rag_used'] = bool(tail)

    # 2. gemma4 — options byte-for-byte as sendMsg sends them.
    t_gen = time.perf_counter()
    first_tok = None
    full = ''
    body = {
        'model': 'gemma4:latest', 'messages': msgs, 'stream': True,
        'keep_alive': '30m', 'think': False,
        'options': {'temperature': 0.85, 'top_p': 0.9, 'num_predict': 120, 'num_ctx': 8192},
    }
    with requests.post(OLLAMA_CHAT, json=body, stream=True, timeout=180) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            obj = json.loads(line)
            tok = (obj.get('message') or {}).get('content') or ''
            if tok:
                if first_tok is None:
                    first_tok = time.perf_counter()
                full += tok
            if obj.get('done'):
                row['prefill_ms'] = round(obj['prompt_eval_duration'] / 1e6) if obj.get('prompt_eval_duration') else None
                row['prompt_tokens'] = obj.get('prompt_eval_count')
                row['eval_count'] = obj.get('eval_count')
                row['done_reason'] = obj.get('done_reason')
    now = time.perf_counter()
    row['first_token_ms'] = int(((first_tok or now) - t_gen) * 1000)
    row['generate_ms'] = int((now - (first_tok or now)) * 1000)

    emo, text = split_emotion(full)
    row['emotion'] = emo
    row['reply_words'] = len(text.split())
    row['reply'] = text

    # 3. TTS — the server reports its own two stages as DURATIONS (bugs.md 79's
    #    clock rule: never compare a python clock with a renderer clock).
    if do_tts and text:
        t_tts = time.perf_counter()
        rs = fish_client.post('/speak', json={'text': text, 'emotion': emo})
        j = rs.get_json() or {}
        row['tts_round_trip_ms'] = int((time.perf_counter() - t_tts) * 1000)
        tm = j.get('timings') or {}
        row['translate_ms'] = tm.get('translate_ms')
        row['fish_ms'] = tm.get('fish_ms')
        row['translator'] = tm.get('translator')
        row['got_audio'] = bool(j.get('audio_b64'))

    row['total_ms'] = int((time.perf_counter() - t0) * 1000)
    return row


def stat(vals):
    v = [x for x in vals if isinstance(x, (int, float))]
    if not v:
        return None
    s = sorted(v)
    return {'n': len(v), 'median': st.median(s), 'min': s[0], 'max': s[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=30)
    ap.add_argument('--no-tts', action='store_true', help='skip Fish Audio (no API spend)')
    ap.add_argument('--capture', default=CAPTURE)
    ap.add_argument('--arm', default='baseline')
    a = ap.parse_args()

    if app_is_running():
        sys.exit('REFUSING TO RUN: Amadeus appears to be open.\n'
                 'gemma4 shares the GPU that renders her (CLAUDE.md 37), and the\n'
                 'Chroma DB takes a write lock. Close the app and re-run.')

    print('\n=== presence latency probe (backlog #186) ===')
    print('This does NOT talk to her. Nothing here reaches her diary, her facts,')
    print('or her relationship score — those all live in the renderer.\n')

    # Baseline hash BEFORE any import — importing kurisu_rag_server re-upserts
    # the behavior rules, so a post-import hash is not a true 'before'.
    pre_import_hash = db_hash()

    base, cap = load_base_messages(a.capture)
    print(f'base prompt: {len(base)} messages from a REAL capture '
          f'({cap.get("at")}, {cap.get("promptTokens")} prompt tokens)')

    import kurisu_rag_server as rag_mod
    import kurisu_fish_server as fish_mod
    rag_client = rag_mod.app.test_client()
    fish_client = fish_mod.app.test_client()

    before = memory_snapshot(rag_mod)
    before['_sqlite_sha256_pre_import'] = pre_import_hash
    print(f'memory BEFORE: {json.dumps(before)}')

    probes = (PROBES * ((a.n // len(PROBES)) + 1))[:a.n]
    print(f'probes: {a.n} ({len(set(probes))} distinct, daily-life set)')
    print(f'TTS: {"OFF (--no-tts)" if a.no_tts else "ON — one Fish call per probe"}\n')

    rows = []
    for i, p in enumerate(probes, 1):
        try:
            r = one_turn(base, p, rag_client, fish_client, not a.no_tts)
        except Exception as e:
            print(f'  {i:>3}/{a.n}  FAILED: {e.__class__.__name__}: {e}')
            continue
        rows.append(r)
        print(f'  {i:>3}/{a.n}  total {r["total_ms"]:>5}ms  '
              f'rag {r["rag_ms"]:>3}  prefill {r.get("prefill_ms")}  '
              f'1st-tok {r["first_token_ms"]:>4}  gen {r["generate_ms"]:>4}  '
              f'tr {r.get("translate_ms")}  fish {r.get("fish_ms")}  '
              f'[{r["emotion"]}] {r["reply_words"]}w')

    after = memory_snapshot(rag_mod)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f'{a.arm}_{time.strftime("%Y%m%d-%H%M%S")}.json')
    json.dump({'arm': a.arm, 'n': len(rows), 'tts': not a.no_tts,
               'base_capture': {'at': cap.get('at'), 'promptTokens': cap.get('promptTokens')},
               'memory_before': before, 'memory_after': after, 'rows': rows},
              open(path, 'w'), indent=2)

    # A turn whose TTS failed has a total_ms that EXCLUDES the TTS stage. Mixing
    # those into one median silently understates the wait, so they are reported
    # apart. (Found live: Fish API credit ran out mid-run on 2026-09-06 and 16 of
    # 30 turns came back without audio.)
    complete = [r for r in rows if r.get('fish_ms')] if not a.no_tts else rows
    partial = [r for r in rows if not r.get('fish_ms')] if not a.no_tts else []

    print(f'\n--- {len(complete)} COMPLETE turns'
          + (f'  ({len(partial)} more had NO audio — reported separately)' if partial else '') + ' ---')
    fields = [('rag', 'rag_ms'), ('prefill', 'prefill_ms'), ('to 1st token', 'first_token_ms'),
              ('generate rest', 'generate_ms'), ('tts round trip', 'tts_round_trip_ms'),
              ('  translate', 'translate_ms'), ('  fish', 'fish_ms'),
              ('TOTAL', 'total_ms'), ('prompt tokens', 'prompt_tokens'),
              ('generated tokens', 'eval_count'), ('reply words', 'reply_words')]
    for label, key in fields:
        st_ = stat([r.get(key) for r in complete])
        if st_:
            print(f'  {label:<18} median {st_["median"]:>7.0f}   min {st_["min"]:>6}  max {st_["max"]:>6}  (n={st_["n"]})')
    if partial:
        st_ = stat([r.get('total_ms') for r in partial])
        print(f'\n  !! {len(partial)} turns produced NO AUDIO. Their totals stop before TTS'
              f' (median {st_["median"]:.0f}ms) and are NOT comparable.')
        print('  !! If this is a Fish Audio credit failure, HER VOICE IS DOWN IN THE APP TOO —')
        print('  !! ttsSpeak falls back to the silent text reveal. Check the log lines above.')

    trunc = sum(1 for r in rows if r.get('done_reason') == 'length')
    if trunc:
        print(f'\n  NOTE: {trunc}/{len(rows)} hit num_predict (done_reason=length) — CLAUDE.md 40.')

    print('\n--- her memory, before vs after ---')
    same = True
    pre = before.pop('_sqlite_sha256_pre_import', None)
    if pre is not None and pre != before.get('_sqlite_sha256'):
        print(f'  file churn at import: {pre} -> {before.get("_sqlite_sha256")}')
        print('    ^ importing kurisu_rag_server re-upserts the 15 STATIC behavior rules,')
        print('      exactly as every normal app launch does. Row counts below prove the')
        print('      CONTENT did not move; only sqlite pages did. Her diary is not involved.')
    for k in before:
        if before[k] != after[k]:
            same = False
            print(f'  CHANGED  {k}: {before[k]} -> {after[k]}')
        else:
            print(f'  unchanged  {k}: {before[k]}')
    print('\n  Diary, facts and relationship live in the renderer\'s localStorage,')
    print('  which python cannot reach. /index-diary was never called.')
    if same:
        print('  Every collection identical, and the DB file hash matches. Nothing was written.')
    else:
        print('  A row count or the file hash MOVED — read the lines above before trusting this run.')
    print(f'\nsaved: {path}')


if __name__ == '__main__':
    main()
