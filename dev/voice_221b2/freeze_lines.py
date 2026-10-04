#!/usr/bin/env python3
"""#221b2 — freeze the 16 Stage 2b lines by the PREREG_221b2 rule, no hand-picking, no network.

Target (8): t2 t4 t6 t8 f2 f4 f6 f8, copied from voice_221/lines.json (frozen since #221).
Guard (8): data/logs/fish.log, "Full tagged text" lines in file order; emotion from the preceding
`Received … emotion=` line; the tag must equal the SHIPPED tag; Japanese = the text after it; keep a
line only if its Japanese has >= 2 sentences; the first 2 per emotion of teasing, sarcastic,
dismissive, curious. fish.log grows and rotates, so the result is frozen in lines_b2.json.
"""
import hashlib, json, os, re, sys
from arms_b2 import AMADEUS, V221, LINES, TARGET, GUARD_EMOTIONS, fs, sentences

if os.path.exists(LINES):
    sys.exit(f'STOP: {LINES} exists — the lines are frozen; delete it only on purpose')
src = {l['id']: l for l in json.load(open(os.path.join(V221, 'lines.json'), encoding='utf-8'))['lines']}
out = [{**src[i], 'id': i, 'role': 'target'} for i in TARGET]

path = os.path.join(AMADEUS, 'data', 'logs', 'fish.log')
raw = open(path, encoding='utf-8').read()
log = raw.splitlines()
emo, en, got = None, None, {e: 0 for e in GUARD_EMOTIONS}
for i, ln in enumerate(log):
    m = re.search(r'\[TTS\] Received: (.*?)\.\.\. emotion=([a-z_]+)', ln)
    if m:
        en, emo = m.group(1), m.group(2)
    if 'Full tagged text' not in ln or emo not in got or got[emo] >= 2 or i + 1 >= len(log):
        continue
    tagged, tag = log[i + 1].strip(), fs.EMOTION_TAGS[emo]
    if not tagged.startswith(tag):
        sys.exit(f'STOP: fish.log line {i + 2}: tag does not match the shipped {emo} tag')
    jp = tagged[len(tag):].strip()
    n = len(sentences(jp))
    if n < 2:
        continue
    got[emo] += 1
    out.append({'id': f'g_{emo}{got[emo]}', 'role': 'guard', 'emotion': emo, 'source': 'fish.log',
                'log_line': i + 2, 'en': en + '…', 'jp': jp, 'n_sentences': n})
missing = {e: 2 - k for e, k in got.items() if k < 2}
if missing:
    sys.exit(f'STOP: not enough guard lines: {missing}')
json.dump({'rule': 'PREREG_221b2.md', 'fish_log_sha256': hashlib.sha256(raw.encode()).hexdigest(),
           'lines': out}, open(LINES, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for l in out:
    print(l['id'], l['emotion'], l.get('log_line', ''), l['jp'][:40])
