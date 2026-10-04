#!/usr/bin/env python3
"""#221 Step 0 — does Fish apply the TOP-LEVEL "speed" field that fish_tts() sends?

Fish's API reference lists speed only as prosody.speed. Same text at top-level speed 0.6
and 1.8 through the shipped fish_tts(). Ratio >= 1.5 -> applied; < 1.15 -> ignored.
If ignored, a positive control with prosody.speed 0.6 / 1.8 shows the effect is detectable.
Changes no arm and no code (PREREG_221.md). Cost: 2 clips (+2 conditional).
Ran 2026-09-30 against fish_tts() at f5f6e82, which still sent a top-level "speed". The #225 cleanup
removed that field, so both branches now send an EXPLICIT payload (the V3 values of that commit).
"""
import json, os
from common import AUDIO, HERE, Guard, synth, duration, fs

TEXT = fs.EMOTION_TAGS['default'] + ' ' + 'いいけどさ、ちゃんと自分も面倒見てよね。ただ、ぐったりして何もかも忘れちゃうなんて、そういう考えはしないでよね？'

guard = Guard()
rows = {}
BASE = {"text": TEXT, "reference_id": fs.FISH_VOICE_ID, "format": "mp3", "mp3_bitrate": 128,
        "latency": "normal", "normalize": True, "chunk_length": 200, "temperature": 0.7,
        "top_p": 0.8, "repetition_penalty": 1.2}
for sp in (0.6, 1.8):
    p = os.path.join(AUDIO, f'step0_toplevel_{sp}.mp3')
    synth(TEXT, p, guard=guard, payload_override={**BASE, "speed": sp})
    rows[f'toplevel_{sp}'] = duration(p)
ratio = rows['toplevel_0.6'] / rows['toplevel_1.8']
verdict = 'applied' if ratio >= 1.5 else 'ignored' if ratio < 1.15 else 'unclear'
print(f'top-level: 0.6 -> {rows["toplevel_0.6"]:.2f}s, 1.8 -> {rows["toplevel_1.8"]:.2f}s, ratio {ratio:.2f} => {verdict}')

if verdict != 'applied':
    for sp in (0.6, 1.8):
        p = os.path.join(AUDIO, f'step0_prosody_{sp}.mp3')
        synth(TEXT, p, guard=guard, payload_override={**BASE, "prosody": {"speed": sp}})
        rows[f'prosody_{sp}'] = duration(p)
    pr = rows['prosody_0.6'] / rows['prosody_1.8']
    print(f'prosody.speed control: 0.6 -> {rows["prosody_0.6"]:.2f}s, 1.8 -> {rows["prosody_1.8"]:.2f}s, ratio {pr:.2f}')

money = guard.report()
json.dump({'text': TEXT, 'durations_s': rows, 'ratio_toplevel': round(ratio, 3), 'verdict': verdict,
           'cost': money},
          open(os.path.join(HERE, 'step0_result.json'), 'w'), indent=2, ensure_ascii=False)
