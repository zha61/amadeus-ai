#!/usr/bin/env python3
"""#221b2 synthesis (PREREG_221b2.md).

  python3 synth_b2.py [--dry]            Stage 2b: A1/A2 (s2-pro, paid, the real shipped fish_tts) and C1/C2
                                         (s2.1-pro-free + the Step 0c prosody) on the 16 lines. #221 A / A' clips
                                         are REUSED (A' = A2 for t2, f2). The first call is a FREE smoke call.
  python3 synth_b2.py --stage3 [--dry]   Stage 3: P (paid s2.1-pro, the exact ship request) on 8 lines.
                                         Refuses unless result_2b.json says C passed.
The guard counts EVERY call as paid, x1.5 (the wallet lags). clips_b2.json is written after every clip,
so a stopped run resumes without paying twice.
"""
import json, os, shutil, sys, time
from arms_b2 import HERE, V221, AUDIO, STEP0C, STAGE3, GUARD_EMOTIONS, load_lines, request_for, prosody, tagged_text
from common import Guard, synth, USD_PER_BYTE, MARGIN   # voice_221/common.py

stage3 = '--stage3' in sys.argv
CAP = 0.10 if stage3 else 0.80   # 2b: raised from 0.55 with Zani's yes (erratum 3); every call as paid, x1.5
OUT = os.path.join(HERE, 'clips_b2.json')
COST = os.path.join(HERE, 'cost_b2.json')
L = load_lines()
if '--dry' in sys.argv and not os.path.exists(STEP0C):
    V = {'volume': -8.5}      # estimate only: prosody does not change the bytes billed; nothing is sent
    print('(dry run before Step 0c: a placeholder prosody is shown)')
else:
    V = prosody()             # exits unless Step 0c passed
clips = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
have = {(c['id'], c['arm'], c['draw']) for c in clips}
cost = json.load(open(COST)) if os.path.exists(COST) else {}

if stage3:
    r = json.load(open(os.path.join(HERE, 'result_2b.json')))
    if not r.get('passes'):
        sys.exit('STOP: 2b did not pass — no Stage 3 (PREREG_221b2)')
    ids = STAGE3 + [f'g_{e}1' for e in GUARD_EMOTIONS]
    todo = [(i, 'P', 1) for i in ids if (i, 'P', 1) not in have]
    spent_before = 0.0
else:
    # 1. reuse #221 A (draw 1) and A' (draw 2) for the target lines — copied, never re-synthesised
    old = {(c['id'], c['arm']): c for c in json.load(open(os.path.join(V221, 'clips.json'), encoding='utf-8'))}
    for i, ln in L.items():
        for draw, arm221 in ((1, 'A'), (2, "A'")):
            c = old.get((i, arm221)) if ln['role'] == 'target' else None
            if c and (i, 'A', draw) not in have:
                assert c['text'] == tagged_text('A', ln['emotion'], ln['jp']), f'{i}: reused text != shipped text'
                dst = os.path.join(AUDIO, f'{i}_A{draw}.mp3')
                shutil.copyfile(os.path.join(V221, c['file']), dst)
                clips.append({'id': i, 'emotion': ln['emotion'], 'role': ln['role'], 'arm': 'A', 'draw': draw,
                              'model': 's2-pro', 'reused_from': f"voice_221/{c['file']}", 'text': c['text'],
                              'bytes': c['bytes'], 'file': os.path.relpath(dst, HERE), 'sha256': c['sha256']})
                have.add((i, 'A', draw))
    # 2. free calls first, so the smoke call is a free call
    todo = [(i, 'C', d) for i in L for d in (1, 2) if (i, 'C', d) not in have]
    todo += [(i, 'A', d) for i in L for d in (1, 2) if (i, 'A', d) not in have]
    spent_before = max([0.0] + [cost[k]['estimated_usd'] for k in ('step0', 'step0b', 'step0c') if k in cost])  # cumulative

reqs = {(i, a, d): request_for(a, L[i]['emotion'], L[i]['jp'], None if a == 'A' else V) for i, a, d in todo}
nbytes = sum(len(reqs[k][0]['text'].encode()) for k in reqs)
paid = sum(len(reqs[k][0]['text'].encode()) for k in reqs if k[1] in ('A', 'P'))
est = nbytes * USD_PER_BYTE * MARGIN
print(f"{'Stage 3' if stage3 else 'Stage 2b'}: {len(todo)} calls ({sum(k[1] in ('A', 'P') for k in reqs)} paid), "
      f"prosody {V}; real cost of paid calls ${paid * USD_PER_BYTE:.4f}; guard estimate ${est:.4f} "
      f"+ earlier ${spent_before:.4f} (every call as paid, x{MARGIN}); cap ${CAP:.2f}")
if spent_before + est > CAP:
    sys.exit('STOP: estimate over the cap — nothing sent')
if '--dry' in sys.argv:
    json.dump(clips, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    sys.exit('dry run: reused clips recorded, nothing sent')

guard = Guard(cap=CAP, spent_before=spent_before)
for k, (i, arm, d) in enumerate(todo):
    payload, model = reqs[(i, arm, d)]
    path = os.path.join(AUDIO, f'{i}_{arm}{d}.mp3')
    t0 = time.perf_counter()
    if arm == 'A':
        sha = synth(payload['text'], path, guard=guard)                        # the real shipped fish_tts path
    else:
        sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
    ms = int((time.perf_counter() - t0) * 1000)       # wall time incl. network; reported, never a gate
    size = os.path.getsize(path)
    if size < 2000:
        sys.exit(f'STOP: {path} is only {size} bytes — not audio')
    clips.append({'id': i, 'emotion': L[i]['emotion'], 'role': L[i]['role'], 'arm': arm, 'draw': d,
                  'model': model, 'voice': payload['reference_id'][:8], 'prosody': payload.get('prosody'),
                  'text': payload['text'], 'bytes': len(payload['text'].encode()),
                  'file': os.path.relpath(path, HERE), 'sha256': sha, 'ms': ms})
    json.dump(clips, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'  {i} {arm}{d} ok ({size} B)' + ('  <- smoke call passed' if k == 0 else ''))
cost['stage3' if stage3 else 'stage2b'] = guard.report()
json.dump(cost, open(COST, 'w'), indent=1)
