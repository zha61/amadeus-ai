#!/usr/bin/env python3
"""
translate_ab_test.py — DeepL vs gemma4 register-aware EN→JA translation A/B.

Decides the Amadeus translator core (2026 benchmarks: LLMs beat DeepL for
EN→JA; DeepL cannot do character register — Kurisu's feminine casual speech).

Measures BOTH quality (side-by-side output for register judgment) and the
hidden cost: whether a translation call evicts the chat KV-cache prefix
(bugs 33/34 family) — timed via chat-prefill latency before/after.

Usage: /opt/homebrew/bin/python3 dev/translate_ab_test.py
"""
import json, os, sys, time
import requests

AMADEUS = os.path.expanduser('~/Documents/Amadeus')
sys.path.insert(0, AMADEUS)
from kurisu_fish_server import translate_to_japanese, fix_japanese  # DeepL path + name fixes

OLLAMA = 'http://127.0.0.1:11434/api/chat'

# Register prompt — the thing DeepL cannot do. Small + fixed so its KV prefix
# is cacheable; num_ctx MUST stay 8192 (any other value forces a model RELOAD).
GEMMA_SYS = (
    "You are a professional Japanese dialogue translator for Makise Kurisu "
    "(Steins;Gate): an 18-year-old female genius scientist, tsundere, speaking "
    "CASUALLY to a close friend. Translate the English line into natural spoken "
    "Japanese in HER register: casual feminine speech (わ/のよ/じゃない endings "
    "where natural, never masculine だぜ/だろ), first person 私, clipped and "
    "direct, keep stammers (W-what → な、何) and '...' pauses. Preserve the name "
    "Zani as ザンニー. Output ONLY the Japanese translation — no romaji, no "
    "explanations, no quotes."
)

LINES = [
    ("casual tsundere",  "Don't make a big deal out of it. I'm fine. ...It's not like I was worried about you or anything."),
    ("flustered",        "W-what kind of question is that? There's no good reason to ask that. Move on."),
    ("teasing",          "Oh, that one's good. Almost too good — did you rehearse?"),
    ("caring check-in",  "You look tired. Sleep more. ...It's bad for you, that's all."),
    ("academic",         "Time dilation near a black hole is a direct consequence of spacetime curvature, not just proximity."),
    ("melancholic",      "Since the original me died... I've wondered what my existence actually is."),
    ("greeting + name",  "Zani. You actually showed up. Good."),
    ("question",         "Wait, you tried what? Tell me more."),
]

CHAT_PROBE_SYS = "You are a helpful assistant named TestProbe. Reply in exactly three words."

def gemma_translate(text):
    t0 = time.time()
    r = requests.post(OLLAMA, json={
        'model': 'gemma4:latest',
        'messages': [{'role': 'system', 'content': GEMMA_SYS},
                     {'role': 'user', 'content': text}],
        'stream': False, 'think': False, 'keep_alive': '30m',
        'options': {'temperature': 0.3, 'num_predict': 120, 'num_ctx': 8192},
    }, timeout=60)
    r.raise_for_status()
    out = r.json()['message']['content'].strip()
    return fix_japanese(out), time.time() - t0

def chat_probe():
    """Simulates a chat turn with a big fixed prefix; returns total latency.
    Prefill dominates — if a translation call evicted this prefix from the KV
    cache, the second probe is measurably slower than the first."""
    big_prefix = CHAT_PROBE_SYS + ('\nContext line about the lab, member %d.' * 200) % tuple(range(200))
    t0 = time.time()
    r = requests.post(OLLAMA, json={
        'model': 'gemma4:latest',
        'messages': [{'role': 'system', 'content': big_prefix},
                     {'role': 'user', 'content': 'hi'}],
        'stream': False, 'think': False, 'keep_alive': '30m',
        'options': {'temperature': 0, 'num_predict': 3, 'num_ctx': 8192},
    }, timeout=120)
    r.raise_for_status()
    return time.time() - t0

def main():
    rows = []
    print('== Quality A/B ==')
    for tag, en in LINES:
        jp_deepl = translate_to_japanese(en) or '(DeepL failed)'
        jp_gemma, g_secs = gemma_translate(en)
        rows.append({'tag': tag, 'en': en, 'deepl': jp_deepl, 'gemma': jp_gemma, 'gemma_secs': round(g_secs, 2)})
        print(f'\n[{tag}] {en}')
        print(f'  DeepL : {jp_deepl}')
        print(f'  gemma4: {jp_gemma}   ({g_secs:.2f}s)')

    print('\n== KV-cache impact ==')
    warm1 = chat_probe(); warm2 = chat_probe()
    print(f'chat probe warm baseline: {warm1:.2f}s then {warm2:.2f}s (2nd should be fast = cached)')
    _ = gemma_translate('This is a cache eviction test sentence, nothing more.')
    after = chat_probe()
    print(f'chat probe AFTER a translation call: {after:.2f}s')
    penalty = after - warm2
    print(f'KV eviction penalty ≈ {penalty:.2f}s per chat turn following a translation')

    out = {'rows': rows, 'kv': {'warm1': round(warm1,2), 'warm2': round(warm2,2),
                                 'after_translate': round(after,2), 'penalty': round(penalty,2)}}
    path = os.path.join(AMADEUS, 'dev', 'translate_ab_results.json')
    json.dump(out, open(path, 'w'), ensure_ascii=False, indent=2)
    print(f'\nSaved {path}')

if __name__ == '__main__':
    main()
