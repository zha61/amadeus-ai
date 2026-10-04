#!/usr/bin/env python3
"""#221b screens (PREREG_221b.md) — reject only. Loop, English bleed and pauses gate; loudness, pitch and
duration are reported. Whisper (mlx large-v3-turbo) uses the GPU, so the app must be CLOSED.
Output: screens_b.json.
"""
import difflib, json, math, os, re, statistics, subprocess, sys
import numpy as np
from arms_b import HERE, load_lines
from common import app_running, internal_pauses, loudness, duration

if app_running():
    sys.exit('STOP: Amadeus is running — Whisper would share the GPU with her rendering')
import mlx_whisper
MODEL = 'mlx-community/whisper-large-v3-turbo'
lines = {l['id']: l for l in load_lines()}
clips = json.load(open(os.path.join(HERE, 'clips_b.json'), encoding='utf-8'))
norm = lambda s: re.sub(r'[\W_]', '', s)


def median_f0(path, sr=16000, n=640, hop=160):
    """Rough autocorrelation pitch (Hz), voiced loud frames only. Used as a RELATIVE measure between arms."""
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    lo, hi, out = sr // 600, sr // 120, []
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n] * np.hanning(n)
        if np.sqrt((fr ** 2).mean()) < 0.02:
            continue
        ac = np.correlate(fr, fr, 'full')[n - 1:]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.4 * ac[0]:
            out.append(sr / k)
    return float(np.median(out)) if out else None


rows = []
for c in clips:
    ln = lines[c['id']]
    path = os.path.join(HERE, c['file'])
    dur, pauses = internal_pauses(path)
    long_ = [p for p in pauses if p > 0.6]
    pause_flag = any(p > 1.2 for p in pauses) or len(long_) > ln['n_sentences'] - 1
    tr = mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, language='ja')['text'].strip()
    latin = re.findall(r'[A-Za-z]{3,}', tr)
    src, hyp = norm(ln['jp']), norm(tr)
    blocks = [b for b in difflib.SequenceMatcher(None, src, hyp, autojunk=False).get_matching_blocks() if b.size >= 2]
    lead = blocks[0].b if blocks else len(hyp)
    rows.append({'id': c['id'], 'emotion': c['emotion'], 'arm': c['arm'], 'draw': c['draw'], 'file': c['file'],
                 'dur': round(dur, 2), 'pauses': pauses, 'pause_flag': pause_flag, 'transcript': tr,
                 'latin': latin, 'lead_unmatched': lead, 'bleed_flag': bool(latin) or lead >= 4,
                 'lufs': loudness(path), 'f0': median_f0(path)})
    r = rows[-1]
    print(f"{c['id']} {c['arm']}{c['draw']:<2} {dur:5.2f}s f0 {r['f0'] or 0:5.1f} lufs {r['lufs']} "
          f"{'PAUSE ' if pause_flag else ''}{'BLEED ' if r['bleed_flag'] else ''}| {tr}")

# loop: longer than 2x the median A duration of its line
a_med = {i: statistics.median(r['dur'] for r in rows if r['id'] == i and r['arm'] == 'A') for i in lines}
for r in rows:
    r['loop_flag'] = r['dur'] > 2 * a_med[r['id']]

A = [r for r in rows if r['arm'] == 'A']
a_lufs = statistics.median(r['lufs'] for r in A)
summary, verdict = {}, {}
for arm in ('A', 'M', 'MV'):
    R = [r for r in rows if r['arm'] == arm]
    st = lambda r: 12 * math.log2(r['f0'] / statistics.median(x['f0'] for x in A if x['id'] == r['id'] and x['f0']))
    summary[arm] = {'n': len(R), 'loop_flags': sum(r['loop_flag'] for r in R),
                    'bleed_flags': sum(r['bleed_flag'] for r in R), 'pause_flags': sum(r['pause_flag'] for r in R),
                    'median_lufs': round(statistics.median(r['lufs'] for r in R), 2),
                    'median_dur_ratio_vs_A': round(statistics.median(r['dur'] / a_med[r['id']] for r in R), 3),
                    'median_pitch_semitones_vs_A': round(statistics.median(st(r) for r in R if r['f0']), 2)}
for arm in ('M', 'MV'):
    s, fails = summary[arm], []
    if s['loop_flags'] >= 2:
        fails.append('loop')
    if s['bleed_flags'] > summary['A']['bleed_flags'] + 2:
        fails.append('bleed')
    if s['pause_flags'] > summary['A']['pause_flags'] + 2:
        fails.append('pauses')
    verdict[arm] = {'pass': not fails, 'fails': fails,
                    'native_lufs_gap_vs_A': round(s['median_lufs'] - summary['A']['median_lufs'], 2)}
print(json.dumps(summary, indent=1))
print(json.dumps(verdict, indent=1))
json.dump({'rows': rows, 'a_median_lufs': a_lufs, 'summary': summary, 'verdict': verdict},
          open(os.path.join(HERE, 'screens_b.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
