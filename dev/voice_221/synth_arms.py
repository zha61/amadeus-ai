#!/usr/bin/env python3
"""#221 Step 3 — synthesise arms A/B/C for the 16 frozen lines, plus A' for t1,t2,f1,f2.

Shipped fish_tts() for every clip; only the text differs (arms.tagged_text). Estimated cost is
printed and checked against the cap BEFORE the first call. Output: clips.json (exact text,
bytes, sha256 and file for every clip). Usage: synth_arms.py [--arms D]
"""
import argparse, json, os, sys
from common import AUDIO, HERE, CAP_USD, USD_PER_BYTE, MARGIN, Guard, synth
from arms import tagged_text

ap = argparse.ArgumentParser()
ap.add_argument('--arms', default="A,B,C,A'")
a = ap.parse_args()
ARMS = a.arms.split(',')
NOISE_IDS = {'t1', 't2', 'f1', 'f2'}

lines = json.load(open(os.path.join(HERE, 'lines.json'), encoding='utf-8'))['lines']
step0 = json.load(open(os.path.join(HERE, 'step0_result.json'), encoding='utf-8'))['cost']['estimated_usd']
OUT = os.path.join(HERE, 'clips.json')
clips = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
spent_before = step0 + sum(c['est_usd'] for c in clips)

todo = []
for ln in lines:
    for arm in ARMS:
        if arm == "A'" and ln['id'] not in NOISE_IDS:
            continue
        if any(c['id'] == ln['id'] and c['arm'] == arm for c in clips):
            continue
        todo.append((ln, arm, tagged_text(arm, ln['emotion'], ln['jp'])))
est = sum(len(t.encode('utf-8')) for _, _, t in todo) * USD_PER_BYTE * MARGIN
print(f'{len(todo)} clips, estimated ${est:.4f} (x{MARGIN} margin); already ${spent_before:.4f}; cap ${CAP_USD:.2f}')
if spent_before + est > CAP_USD:
    sys.exit('STOP: the estimate is over the cap — nothing was sent')

guard = Guard(spent_before=spent_before)
for ln, arm, text in todo:
    safe = arm.replace("'", 'p')
    path = os.path.join(AUDIO, f'{ln["id"]}_{safe}.mp3')
    sha = synth(text, path, guard=guard)
    clips.append({'id': ln['id'], 'emotion': ln['emotion'], 'arm': arm, 'text': text,
                  'bytes': len(text.encode('utf-8')),
                  'est_usd': round(len(text.encode('utf-8')) * USD_PER_BYTE * MARGIN, 5),
                  'file': os.path.relpath(path, HERE), 'sha256': sha})
    json.dump(clips, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)  # after EVERY clip
    print(f'  {ln["id"]} {arm:2s} ok')
money = guard.report()
json.dump(money, open(os.path.join(HERE, f'cost_{"_".join(a.replace(chr(39), "p") for a in ARMS)}.json'), 'w'), indent=1)
