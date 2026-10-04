#!/usr/bin/env python3
"""#221b Stage 2a synthesis (PREREG_221b.md): M1 M2 MV1 MV2 on the 8 pilot lines (free model), and A2 on
s2-pro (shipped fish_tts) for the pilot lines that have no #221 A' clip. A1/A2 already on disk are REUSED.

The guard counts every call as if paid (a free model that bills by mistake stays bounded). The FIRST clip
is a smoke call on the free model: if it fails, nothing else is sent. clips_b.json is written after every
clip, so a stopped run resumes without paying twice.
"""
import json, os, shutil, sys
from arms_b import HERE, V221, AUDIO, ARMS, load_lines, request_for, tagged_text
from common import Guard, synth, USD_PER_BYTE, MARGIN, app_running   # voice_221/common.py

CAP = 0.30
OUT = os.path.join(HERE, 'clips_b.json')
old = {(c['id'], c['arm']): c for c in json.load(open(os.path.join(V221, 'clips.json'), encoding='utf-8'))}
clips = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
have = {(c['id'], c['arm'], c['draw']) for c in clips}

# 1. reuse #221 A (draw 1) and A' (draw 2) — copied, never re-synthesised
for ln in load_lines():
    for draw, arm221 in ((1, 'A'), (2, "A'")):
        c = old.get((ln['id'], arm221))
        if c and (ln['id'], 'A', draw) not in have:
            dst = os.path.join(AUDIO, f"{ln['id']}_A{draw}.mp3")
            shutil.copyfile(os.path.join(V221, c['file']), dst)
            assert c['text'] == tagged_text('A', ln['emotion'], ln['jp']), 'reused A clip text != shipped text'
            clips.append({'id': ln['id'], 'emotion': ln['emotion'], 'arm': 'A', 'draw': draw, 'model': 's2-pro',
                          'reused_from': f"voice_221/{c['file']}", 'text': c['text'], 'bytes': c['bytes'],
                          'file': os.path.relpath(dst, HERE), 'sha256': c['sha256']})
            have.add((ln['id'], 'A', draw))

# 2. the calls still needed; the free model first, so the smoke call is a free-model call
todo = []
for arm in ('M', 'MV', 'A'):
    for ln in load_lines():
        for draw in (1, 2):
            if (ln['id'], arm, draw) not in have:
                todo.append((ln, arm, draw))
payloads = {(ln['id'], arm, draw): request_for(arm, ln['emotion'], ln['jp']) for ln, arm, draw in todo}
est = sum(len(payloads[(ln['id'], a, d)][0]['text'].encode()) for ln, a, d in todo) * USD_PER_BYTE * MARGIN
print(f'{len(todo)} calls ({sum(a == "A" for _, a, _ in todo)} paid s2-pro), guard estimate ${est:.4f} '
      f'(every call counted as paid), cap ${CAP:.2f}')
if est > CAP:
    sys.exit('STOP: estimate over the cap — nothing sent')
if '--dry' in sys.argv:
    json.dump(clips, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    sys.exit('dry run: reused clips recorded, nothing sent')

guard = Guard(cap=CAP)
for k, (ln, arm, draw) in enumerate(todo):
    payload, model = payloads[(ln['id'], arm, draw)]
    path = os.path.join(AUDIO, f"{ln['id']}_{arm}{draw}.mp3")
    if arm == 'A':
        sha = synth(payload['text'], path, guard=guard)                 # the real shipped fish_tts path
    else:
        sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
    size = os.path.getsize(path)
    if size < 2000:
        sys.exit(f'STOP: {path} is only {size} bytes — not audio')
    clips.append({'id': ln['id'], 'emotion': ln['emotion'], 'arm': arm, 'draw': draw, 'model': model,
                  'voice': payload['reference_id'][:8], 'text': payload['text'],
                  'bytes': len(payload['text'].encode()), 'file': os.path.relpath(path, HERE), 'sha256': sha})
    json.dump(clips, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"  {ln['id']} {arm}{draw} ok ({size} B)" + ('  <- smoke call passed' if k == 0 else ''))
money = guard.report()
json.dump(money, open(os.path.join(HERE, 'cost_2a.json'), 'w'), indent=1)
print('app running during synthesis:', app_running())
