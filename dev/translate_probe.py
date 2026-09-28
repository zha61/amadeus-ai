#!/usr/bin/env python3
"""
translate_probe.py — decompose the translate step (backlog #196).

WHY THIS EXISTS
    #196 says to measure translate with dev/latency_probe.py.  That tool
    reports translate_ms only when it also calls Fish Audio: `--no-tts` skips
    the whole /speak request (latency_probe.py:212), so the field is never
    populated.  Zani asked for a baseline that spends NO Fish credit.

    So this probe measures the translate call on its own.  It is one Ollama
    request per input and touches nothing else — no Fish Audio, no Chroma, no
    diary, no facts, no relationship.  It cannot write to her memory because it
    never opens any of those stores.

WHAT IT ADDS OVER A WALL-CLOCK NUMBER
    The live 1270ms is one opaque figure.  Ollama reports the split, so this
    records load / prefill / decode separately.  Each has a different fix:
      * prefill-bound  -> shortening KURISU_REGISTER_PROMPT can win
      * decode-bound   -> only fewer output tokens or a faster model can win
      * load-bound     -> a keep_alive problem (CLAUDE.md 44), not a prompt one

BYTE-EXACTNESS
    The system prompt and the sampling options are read from the SHIPPED
    kurisu_fish_server.py, and verify_shipped_config() asserts the option
    values still match the ones in translate_via_gemma().  If someone edits
    that function without editing this probe, the probe FAILS LOUDLY rather
    than reporting a stale arm as the baseline.  (Same idea as the anchor
    checks in dev/check.js.)

APP MUST BE CLOSED — it calls gemma4, which runs on the GPU that renders her
(CLAUDE.md 37).

Usage:
    python3 dev/translate_probe.py                    # n=30 baseline, no Fish spend
    python3 dev/translate_probe.py --arm short_prompt # label a Phase-1 arm
    python3 dev/translate_probe.py --kv               # ALSO re-measure KV eviction
"""

import argparse
import datetime as dt
import inspect
import json
import glob
import os
import re
import statistics as st
import subprocess
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

OLLAMA_CHAT = 'http://127.0.0.1:11434/api/chat'
OLLAMA_PS = 'http://127.0.0.1:11434/api/ps'
OLLAMA_VERSION = 'http://127.0.0.1:11434/api/version'
OUT_DIR = os.path.join(HERE, 'translate_arms')
EMO_TAG = re.compile(r'^\s*\[EMOTION:[^\]]*\]\s*|\[[a-z_]+\]', re.I)

# The shipped translate call.  Kept here so an ARM can override one field and
# every other field stays byte-identical to production.
SHIPPED_OPTS = {'temperature': 0.3, 'num_predict': 150, 'num_ctx': 8192}


def die(msg):
    sys.exit(f'[translate_probe] REFUSING: {msg}')


def assert_app_closed():
    """CLAUDE.md 37 — never call gemma4 while she is rendering."""
    r = subprocess.run(['pgrep', '-f', 'Amadeus.app'], capture_output=True, text=True)
    if r.stdout.strip():
        die('the Amadeus app is running. Close it — gemma4 shares her GPU (CLAUDE.md 37).')


def verify_shipped_config():
    """Read the real translate_via_gemma() and prove this probe matches it."""
    import kurisu_fish_server as fish
    src = inspect.getsource(fish.translate_via_gemma)
    problems = []
    for k, v in SHIPPED_OPTS.items():
        if f"'{k}': {v}" not in src:
            problems.append(f"{k}={v} not found in shipped translate_via_gemma()")
    if "'model': 'gemma4:latest'" not in src:
        problems.append("model is no longer gemma4:latest")
    if problems:
        die('this probe no longer matches the shipped code:\n  - ' + '\n  - '.join(problems))
    return fish.KURISU_REGISTER_PROMPT, fish


def load_inputs():
    """Real replies from the Sep 6 latency probe = real translate inputs.

    The renderer strips the emotion tag before /speak (parsEmo, bugs.md 5/8),
    so the tag is stripped here too.  Anything else would measure a longer
    string than production ever sends."""
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(HERE, 'latency_arms', '*.json'))):
        d = json.load(open(f))
        for row in d.get('rows', []):
            t = (row.get('reply') or '').strip()
            t = EMO_TAG.sub('', t).strip()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def translate_deepl_once(text, fish):
    """The shipped DeepL fallback ([kurisu_fish_server.py:409]), timed.
    It is a network call, so there is no load/prefill/decode split to report —
    and no GPU contention with her Live2D rendering (CLAUDE.md 37)."""
    t0 = time.perf_counter()
    out = fish.translate_via_deepl(text)
    wall_ms = int((time.perf_counter() - t0) * 1000)
    return {
        'in': text, 'in_words': len(text.split()), 'out': (out or '').strip(),
        'wall_ms': wall_ms, 'load_ms': 0, 'prefill_ms': 0, 'prefill_tokens': None,
        'decode_ms': 0, 'decode_tokens': None, 'done_reason': 'deepl' if out else 'FAILED',
    }


def translate_once(text, system_prompt, opts, model='gemma4:latest'):
    """One shipped-shape translate call, with Ollama's own counters kept."""
    t0 = time.perf_counter()
    r = requests.post(OLLAMA_CHAT, json={
        'model': model,
        'messages': [{'role': 'system', 'content': system_prompt},
                     {'role': 'user', 'content': text}],
        'stream': False, 'think': False, 'keep_alive': '30m',
        'options': opts,
    }, timeout=60)
    r.raise_for_status()
    wall_ms = int((time.perf_counter() - t0) * 1000)
    j = r.json()
    ns = lambda k: round(j[k] / 1e6) if j.get(k) else 0
    return {
        'in': text,
        'in_words': len(text.split()),
        'out': j['message']['content'].strip(),
        'wall_ms': wall_ms,
        'load_ms': ns('load_duration'),
        'prefill_ms': ns('prompt_eval_duration'),
        'prefill_tokens': j.get('prompt_eval_count'),
        'decode_ms': ns('eval_duration'),
        'decode_tokens': j.get('eval_count'),
        'done_reason': j.get('done_reason'),
    }


def chat_probe():
    """A chat turn with a big fixed prefix.  Prefill dominates, so if a
    translate call evicted this prefix from the KV cache the next probe is
    measurably slower.  Same construction as dev/translate_ab_test.py so the
    July +0.57s figure and this one are comparable."""
    big = 'You are a helpful assistant named TestProbe. Reply in exactly three words.' + \
          ('\nContext line about the lab, member %d.' * 200) % tuple(range(200))
    t0 = time.perf_counter()
    r = requests.post(OLLAMA_CHAT, json={
        'model': 'gemma4:latest',
        'messages': [{'role': 'system', 'content': big}, {'role': 'user', 'content': 'hi'}],
        'stream': False, 'think': False, 'keep_alive': '30m',
        'options': {'temperature': 0, 'num_predict': 3, 'num_ctx': 8192},
    }, timeout=120)
    r.raise_for_status()
    return time.perf_counter() - t0


def stat(rows, key):
    v = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    if not v:
        return None
    s = sorted(v)
    return {'n': len(s), 'median': st.median(s), 'min': s[0], 'max': s[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=30)
    ap.add_argument('--arm', default='baseline')
    ap.add_argument('--kv', action='store_true', help='also re-measure the KV eviction penalty')
    ap.add_argument('--num-predict', type=int, default=None, help='ARM: override num_predict')
    ap.add_argument('--engine', choices=['gemma4', 'deepl'], default='gemma4')
    ap.add_argument('--model', default='gemma4:latest', help='ARM: translate with a different local model')
    a = ap.parse_args()

    assert_app_closed()
    system_prompt, fish = verify_shipped_config()
    is_deepl = a.engine == 'deepl'
    if is_deepl and a.arm == 'baseline':
        a.arm = 'deepl'
    one = ((lambda t: translate_deepl_once(t, fish)) if is_deepl
           else (lambda t: translate_once(t, system_prompt, opts, a.model)))
    opts = dict(SHIPPED_OPTS)
    if a.num_predict is not None:
        opts['num_predict'] = a.num_predict

    ver = requests.get(OLLAMA_VERSION, timeout=5).json().get('version')
    ps = requests.get(OLLAMA_PS, timeout=5).json()

    inputs = load_inputs()
    if not inputs:
        die('no replies found in dev/latency_arms/ — nothing real to translate.')
    inputs = (inputs * ((a.n // len(inputs)) + 1))[:a.n]

    print(f'== translate_probe  arm={a.arm}  engine={a.engine}  n={a.n} ==')
    print(f'Ollama {ver}   model={a.model}   opts={opts if not is_deepl else "(n/a — DeepL)"}')
    print(f'prompt: {len(system_prompt)} chars   inputs: {len(set(inputs))} distinct')
    print('Fish Audio: NOT CALLED — this probe spends no TTS credit.\n')
    for m in ps.get('models', []):
        print(f'  loaded: {m.get("name")}  vram={m.get("size_vram")}  expires={m.get("expires_at")}')
    print()

    print('warm-up call (discarded — a cold load is not the steady state)...')
    w = one(inputs[0])
    print(f'  warm-up wall={w["wall_ms"]}ms load={w["load_ms"]}ms\n')

    rows = []
    for i, text in enumerate(inputs, 1):
        r = one(text)
        rows.append(r)
        if is_deepl:
            print(f'{i:3d}/{a.n}  wall {r["wall_ms"]:5d}ms  (network)                            {r["out"][:34]}')
        else:
            print(f'{i:3d}/{a.n}  wall {r["wall_ms"]:5d}ms  = load {r["load_ms"]:4d} + '
                  f'prefill {r["prefill_ms"]:4d} ({r["prefill_tokens"]}t) + '
                  f'decode {r["decode_ms"]:4d} ({r["decode_tokens"]}t)   {r["out"][:34]}')

    kv = None
    if a.kv:
        print('\n== KV eviction re-measure (the July +0.57s, on this Ollama) ==')
        w1, w2 = chat_probe(), chat_probe()
        _ = translate_once('This is a cache eviction test sentence, nothing more.', system_prompt, opts)
        after = chat_probe()
        kv = {'warm1_s': round(w1, 2), 'warm2_s': round(w2, 2),
              'after_translate_s': round(after, 2), 'penalty_s': round(after - w2, 2)}
        print(f'  chat probe warm: {w1:.2f}s then {w2:.2f}s (2nd should be cached)')
        print(f'  chat probe AFTER a translate: {after:.2f}s')
        print(f'  penalty = {after - w2:+.2f}s per chat turn following a translate')

    summary = {k: stat(rows, k) for k in
               ('wall_ms', 'load_ms', 'prefill_ms', 'prefill_tokens',
                'decode_ms', 'decode_tokens', 'in_words')}
    print('\n== MEDIANS ==')
    for k, s in summary.items():
        if s:
            print(f'  {k:16s} median {s["median"]:8.1f}   min {s["min"]:6}  max {s["max"]:6}')

    med = summary['wall_ms']['median']
    pre, dec = summary['prefill_ms']['median'], summary['decode_ms']['median']
    if med and not is_deepl:
        print(f'\n  prefill is {100*pre/med:4.1f}% of the call')
        print(f'  decode  is {100*dec/med:4.1f}% of the call')
    if is_deepl:
        failed = [r for r in rows if r['done_reason'] == 'FAILED']
        print(f'  DeepL failures: {len(failed)}/{len(rows)}')
    else:
        trunc = [r for r in rows if r.get('done_reason') == 'length']
        print(f'  truncated (done_reason=length): {len(trunc)}/{len(rows)}   '
              f'(CLAUDE.md 40 — headroom {opts["num_predict"]/max(1,summary["decode_tokens"]["max"]):.1f}x '
              f'against the MAX, not the median)')

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f'{a.arm}_{dt.datetime.now():%Y%m%d-%H%M%S}.json')
    json.dump({'arm': a.arm, 'engine': a.engine, 'model': a.model, 'n': len(rows), 'ollama': ver, 'opts': opts,
               'prompt_chars': len(system_prompt), 'summary': summary,
               'kv': kv, 'rows': rows}, open(path, 'w'), ensure_ascii=False, indent=2)
    print(f'\nSaved {path}')


if __name__ == '__main__':
    main()
