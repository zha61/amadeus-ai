#!/usr/bin/env python3
"""#221 Step 2 — select the 16 fixed Japanese test lines by the PREREG_221 rule, no hand-picking.

Calls gemma4 through the SHIPPED translate_via_gemma() for E1 lines, one call each, so the
app must be CLOSED (CLAUDE.md 37). Output: lines.json (frozen; never re-translated).
Dedupe key: English = reply without its first word, lowercase, letters only (so "What? Don't…"
and "W-what? Don't…" collide). Japanese (fish.log) has no word spaces, so its key is the
whole line with punctuation and spaces removed.
"""
import json, os, re, sys
from common import AMADEUS, HERE, app_running, fs
from arms import sentences

if app_running():
    sys.exit('STOP: Amadeus is running — gemma4 must not be called (CLAUDE.md 37)')
OUT = os.path.join(HERE, 'lines.json')
if os.path.exists(OUT):
    sys.exit(f'STOP: {OUT} exists — the lines are frozen; delete it only on purpose')

EMO = re.compile(r'^\s*\[(?:EMOTION:)?([A-Za-z_]+)\]\s*')
WANT = {'tsundere': (4, 4), 'flustered': (None, 7)}   # (from fish.log, from E1); None = all


def key_en(t):
    return re.sub(r'[^a-z]', '', ' '.join(t.split()[1:]).lower())


def key_ja(t):
    return re.sub(r'[\W_]', '', t)


# ── fish.log ──
fish = []
emo, en = None, None
lines = open(os.path.join(AMADEUS, 'data', 'logs', 'fish.log'), encoding='utf-8').read().splitlines()
for i, ln in enumerate(lines):
    m = re.search(r'\[TTS\] Received: (.*?)\.\.\. emotion=([a-z_]+)', ln)
    if m:
        en, emo = m.group(1), m.group(2)
    if 'Full tagged text' in ln and i + 1 < len(lines):
        tagged = lines[i + 1].strip()
        tag = fs.EMOTION_TAGS.get(emo, '')
        if not tag or not tagged.startswith(tag):
            sys.exit(f'STOP: fish.log line {i + 2}: tag does not match the shipped {emo} tag')
        fish.append({'log_line': i + 2, 'emotion': emo, 'en_prefix': en, 'jp': tagged[len(tag):].strip()})

picked, rejected, seen = [], [], set()
for emotion, (n_fish, _) in WANT.items():
    got = 0
    for r in fish:
        if r['emotion'] != emotion or (n_fish is not None and got >= n_fish):
            continue
        k = key_ja(r['jp'])
        if k in seen:
            rejected.append({**r, 'why': 'duplicate'}); continue
        if len(sentences(r['jp'])) < 2:
            rejected.append({**r, 'why': '<2 Japanese sentences'}); continue
        seen.add(k)
        picked.append({'source': 'fish.log', 'emotion': emotion, 'context': f'her reply: "{r["en_prefix"]}…"',
                       'en': r['en_prefix'] + '…', 'jp': r['jp'], 'log_line': r['log_line']})
        got += 1

# ── E1_HEAD (shipped SYSTEM_PROMPT, RAG on, stage 3) ──
e1 = json.load(open(os.path.join(AMADEUS, 'dev', 'canon_arms', 'E1_HEAD.txt.json'), encoding='utf-8'))
calls = 0
for emotion, (_, n_e1) in WANT.items():
    got = 0
    for r in e1:
        if got >= n_e1:
            break
        m = EMO.match(r['reply'])
        if not m or m.group(1).lower() != emotion:
            continue
        body = EMO.sub('', r['reply']).strip()
        k = key_en(body)
        if k in seen:
            rejected.append({'probe': r['probe'], 'emotion': emotion, 'en': body, 'why': 'duplicate'}); continue
        seen.add(k)
        jp = fs.translate_via_gemma(body)          # the shipped translator, one call, frozen
        calls += 1
        if not jp:
            sys.exit(f'STOP: translate_via_gemma returned nothing for: {body}')
        if len(sentences(jp)) < 2:
            rejected.append({'probe': r['probe'], 'emotion': emotion, 'en': body, 'jp': jp,
                             'why': '<2 Japanese sentences'}); continue
        picked.append({'source': 'E1_HEAD', 'emotion': emotion, 'context': f'Zani: "{r["probe"]}"',
                       'en': body, 'jp': jp})
        got += 1
        print(f'  {emotion:9s} {jp}')

for emotion in WANT:
    n = sum(p['emotion'] == emotion for p in picked)
    if n != 8:
        sys.exit(f'STOP: {emotion} has {n} lines, not 8')
# stable ids: t1..t8, f1..f8 in selection order (fish.log first)
for emotion, pre in (('tsundere', 't'), ('flustered', 'f')):
    for j, p in enumerate([p for p in picked if p['emotion'] == emotion], 1):
        p['id'] = f'{pre}{j}'
        p['n_sentences'] = len(sentences(p['jp']))
picked.sort(key=lambda p: (p['id'][0] != 't', int(p['id'][1:])))
json.dump({'rule': 'PREREG_221.md', 'gemma4_calls': calls, 'translate_prompt': fs.KURISU_REGISTER_PROMPT,
           'lines': picked, 'rejected': rejected},
          open(OUT, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'wrote {OUT}: {len(picked)} lines, {len(rejected)} rejected, {calls} gemma4 calls')
