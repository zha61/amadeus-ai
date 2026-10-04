#!/usr/bin/env python3
"""#221 Step 4 — reject-only screens (PREREG_221): pauses, English bleed, loudness.

Pure local. Whisper (mlx, large-v3-turbo, the model the app uses) loads ~1.6 GB on the GPU,
so the app must be CLOSED. Output: screens.json.
"""
import difflib, json, os, re, statistics, sys
from common import HERE, app_running, internal_pauses, loudness

if app_running():
    sys.exit('STOP: Amadeus is running — Whisper would share the GPU with her rendering')
import mlx_whisper
MODEL = 'mlx-community/whisper-large-v3-turbo'

lines = {l['id']: l for l in json.load(open(os.path.join(HERE, 'lines.json'), encoding='utf-8'))['lines']}
clips = json.load(open(os.path.join(HERE, 'clips.json'), encoding='utf-8'))
norm = lambda s: re.sub(r'[\W_]', '', s)

rows = []
for c in clips:
    ln = lines[c['id']]
    path = os.path.join(HERE, c['file'])
    dur, pauses = internal_pauses(path)
    boundaries = ln['n_sentences'] - 1
    long_ = [p for p in pauses if p > 0.6]
    pause_flag = any(p > 1.2 for p in pauses) or len(long_) > boundaries
    tr = mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, language='ja')['text'].strip()
    latin = re.findall(r'[A-Za-z]{3,}', tr)
    src, hyp = norm(ln['jp']), norm(tr)
    blocks = [b for b in difflib.SequenceMatcher(None, src, hyp, autojunk=False).get_matching_blocks() if b.size >= 2]
    lead = blocks[0].b if blocks else len(hyp)
    bleed_flag = bool(latin) or lead >= 4
    rows.append({'id': c['id'], 'emotion': c['emotion'], 'arm': c['arm'], 'dur': round(dur, 2),
                 'pauses': pauses, 'boundaries': boundaries, 'pause_flag': pause_flag,
                 'transcript': tr, 'latin': latin, 'lead_unmatched': lead, 'bleed_flag': bleed_flag,
                 'lufs': loudness(path)})
    print(f"{c['id']:3s} {c['arm']:2s} dur {dur:5.2f} pauses {pauses} {'PAUSE' if pause_flag else ''} "
          f"{'BLEED' if bleed_flag else ''} lead={lead} | {tr}")

summary = {}
for arm in ('A', 'B', 'C', "A'", 'D'):
    r = [x for x in rows if x['arm'] == arm]
    if not r:
        continue
    summary[arm] = {'n': len(r), 'pause_flags': sum(x['pause_flag'] for x in r),
                    'bleed_flags': sum(x['bleed_flag'] for x in r),
                    'median_lufs': round(statistics.median(x['lufs'] for x in r), 2),
                    'median_dur': round(statistics.median(x['dur'] for x in r), 2),
                    'max_pause': max((max(x['pauses']) if x['pauses'] else 0) for x in r)}
A = summary['A']
bleed_trusted = A['bleed_flags'] <= 2
verdict = {}
for arm, s in summary.items():
    if arm in ('A', "A'"):
        continue
    fails = []
    if s['pause_flags'] > A['pause_flags'] + 2:
        fails.append('pauses')
    if bleed_trusted and s['bleed_flags'] > A['bleed_flags'] + 2:
        fails.append('bleed')
    verdict[arm] = {'pass': not fails, 'fails': fails,
                    'loudness_confound': s['median_lufs'] - A['median_lufs'] > 2}
print(json.dumps(summary, indent=1))
print('bleed screen trusted:', bleed_trusted)
print(json.dumps(verdict, indent=1))
json.dump({'rows': rows, 'summary': summary, 'bleed_trusted': bleed_trusted, 'verdict': verdict},
          open(os.path.join(HERE, 'screens.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
