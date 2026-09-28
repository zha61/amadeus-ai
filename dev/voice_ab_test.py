#!/usr/bin/env python3
"""
voice_ab_test.py — A/B test of Fish Audio prosody-tag density vs naturalness.

Synthesizes the same 2 Kurisu lines through 4 pipeline variants, saves MP3s to
dev/voice_test/, and measures pause structure + speech rate with ffmpeg.

Variants:
  V0_current  — exact current pipeline (dense tags, compute_speed, temp 0.8)
  V1_thinned  — sentence-boundary pauses + ellipsis only; no comma tags,
                no re-anchors, no sigh/emphasis. Same speed as V0.
  V2_minimal  — NO inline tags (Fish handles JP punctuation natively);
                emotion style tag only; fixed speed 1.1
  V3_min_norm — V2 + normalize:True + temperature 0.7

Human-speech reference (research):
  within-sentence pauses ~0.2-0.6s | between sentences 0.6-1.2s
  >1.5s mid-utterance = unnatural | high pause variance = jerky
"""
import sys, os, json, subprocess, re, statistics

AMADEUS = os.path.expanduser('~/Documents/Amadeus')
sys.path.insert(0, AMADEUS)
OUT = os.path.join(AMADEUS, 'dev', 'voice_test')
os.makedirs(OUT, exist_ok=True)

import requests
from kurisu_fish_server import (translate_to_japanese, add_prosody_tags,
                                compute_speed, EMOTION_TAGS,
                                FISH_API_KEY, FISH_VOICE_ID, FISH_API_URL, FISH_MODEL)

LINES = [
    ("tsundere", "Don't make a big deal out of it. I'm fine... It's not like I was worried about you, or anything. Did you even eat today?"),
    ("calm",     "Slow evening. I was just sitting with my thoughts... Some nights are like that. How was your day?"),
]

def fish_call(text, speed, temp, normalize):
    payload = {
        "text": text, "reference_id": FISH_VOICE_ID, "format": "mp3",
        "mp3_bitrate": 128, "latency": "normal", "normalize": normalize,
        "chunk_length": 200, "temperature": temp, "top_p": 0.8,
        "repetition_penalty": 1.2, "speed": round(max(0.5, min(2.0, speed)), 2),
    }
    headers = {"Authorization": f"Bearer {FISH_API_KEY}",
               "Content-Type": "application/json", "model": FISH_MODEL}
    r = requests.post(FISH_API_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content

def thin_tags(jp):
    """V1: sentence boundaries + ellipsis hesitation only."""
    t = jp.replace("…", "… [pause]").replace("...", "... [pause]")
    t = t.replace("。", "。[short pause]")
    return re.sub(r"  +", " ", t).strip()

def analyze(path):
    """ffmpeg silencedetect → pause list; ffprobe → duration."""
    dur = float(subprocess.run(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())
    res = subprocess.run(
        ['ffmpeg', '-i', path, '-af', 'silencedetect=noise=-35dB:d=0.15',
         '-f', 'null', '-'], capture_output=True, text=True)
    sil = [float(m) for m in re.findall(r'silence_duration: ([\d.]+)', res.stderr)]
    return dur, sil

results = []
for emo, en in LINES:
    jp = translate_to_japanese(en)
    print(f'\n=== [{emo}] JP: {jp}')
    v0_speed = compute_speed(emo, jp)
    style = EMOTION_TAGS.get(emo, "")
    variants = {
        'V0_current':  (f'{style} {add_prosody_tags(jp, emo)}'.strip(), v0_speed, 0.8, False),
        'V1_thinned':  (f'{style} {thin_tags(jp)}'.strip(),             v0_speed, 0.8, False),
        'V2_minimal':  (f'{style} {jp}'.strip(),                        1.1,      0.8, False),
        'V3_min_norm': (f'{style} {jp}'.strip(),                        1.1,      0.7, True),
    }
    for name, (text, speed, temp, norm) in variants.items():
        fn = os.path.join(OUT, f'{emo}_{name}.mp3')
        audio = fish_call(text, speed, temp, norm)
        open(fn, 'wb').write(audio)
        dur, sil = analyze(fn)
        voiced = dur - sum(sil)
        rate = len(jp.replace(' ', '')) / voiced if voiced > 0 else 0
        row = {'line': emo, 'variant': name, 'speed': speed, 'dur': round(dur, 2),
               'pauses': [round(s, 2) for s in sil],
               'max_pause': round(max(sil), 2) if sil else 0,
               'pause_total': round(sum(sil), 2),
               'chars_per_sec_voiced': round(rate, 2)}
        results.append(row)
        print(f'  {name:12s} dur={row["dur"]:5.2f}s pauses={row["pauses"]} '
              f'max={row["max_pause"]}s rate={row["chars_per_sec_voiced"]} ch/s (speed={speed})')

json.dump(results, open(os.path.join(OUT, 'results.json'), 'w'), indent=2)
print(f'\nSaved MP3s + results.json → {OUT}')
