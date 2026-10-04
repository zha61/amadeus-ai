#!/usr/bin/env python3
"""#221b2 screens (PREREG_221b2.md) — reject only. Whisper (mlx large-v3-turbo) uses the GPU: app CLOSED.

  python3 screens_b2.py            Stage 2b: A and C clips -> screens_b2.json
  python3 screens_b2.py --stage3   Stage 3: P clips vs the C clips of the same lines -> screens_s3.json
  python3 screens_b2.py selftest   verdict rules on synthetic rows (no audio, no Whisper)
"""
import difflib, json, math, os, re, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))


def verdict_2b(rows):
    """PREREG gates for C over its 32 clips vs A's 32 clips."""
    A = [r for r in rows if r['arm'] == 'A']
    C = [r for r in rows if r['arm'] == 'C']
    n = lambda R, k: sum(bool(r[k]) for r in R)
    gap = st.median(r['lufs'] for r in C) - st.median(r['lufs'] for r in A)
    fails = []
    if n(C, 'loop_flag') >= 2:
        fails.append('loop')
    if n(C, 'bleed_flag') > n(A, 'bleed_flag') + 4:
        fails.append('bleed')
    if n(C, 'pause_flag') > n(A, 'pause_flag') + 4:
        fails.append('pauses')
    if abs(gap) > 1.5:
        fails.append('level')
    return {'pass': not fails, 'fails': fails, 'native_lufs_gap_C_vs_A': round(gap, 2),
            'flags': {a: {k: n(R, k) for k in ('loop_flag', 'bleed_flag', 'pause_flag')} for a, R in (('A', A), ('C', C))},
            'C_true_peak_over_-1': sum(r['peak_dbtp'] is not None and r['peak_dbtp'] > -1.0 for r in C),
            'A_true_peak_over_-1': sum(r['peak_dbtp'] is not None and r['peak_dbtp'] > -1.0 for r in A),
            'median_plr_db (reported)': {a: round(st.median(r['peak_dbtp'] - r['lufs'] for r in R if r['peak_dbtp'] is not None), 2)
                                         for a, R in (('A', A), ('C', C))}}


def verdict_s3(P, C):
    """PREREG Stage 3: the paid model matches the free model (medians over the 8 lines)."""
    by = lambda i, k: st.median(r[k] for r in C if r['id'] == i and r[k])
    lu = st.median(abs(p['lufs'] - by(p['id'], 'lufs')) for p in P)
    dur = st.median(p['dur'] / by(p['id'], 'dur') for p in P)
    semi = st.median(12 * math.log2(p['f0'] / by(p['id'], 'f0')) for p in P if p['f0'])
    checks = {'level': lu <= 1.5, 'duration': 0.90 <= dur <= 1.10, 'pitch': abs(semi) <= 1.0,
              'loop': not any(p['loop_flag'] for p in P), 'bleed': sum(p['bleed_flag'] for p in P) <= 1}
    return {'pass': all(checks.values()), 'checks': checks, 'median_abs_lufs_diff': round(lu, 2),
            'median_dur_ratio': round(dur, 3), 'median_pitch_semitones': round(semi, 2)}


def main(stage3):
    from arms_b2 import load_lines
    from common import app_running, internal_pauses, loudness            # voice_221/common.py
    from step0 import true_peak
    from measure_b2 import median_f0
    if app_running():
        sys.exit('STOP: Amadeus is running — Whisper would share the GPU with her rendering')
    import mlx_whisper
    MODEL = 'mlx-community/whisper-large-v3-turbo'
    L = load_lines()
    clips = json.load(open(os.path.join(HERE, 'clips_b2.json'), encoding='utf-8'))
    arms = ('P',) if stage3 else ('A', 'C')
    norm = lambda s: re.sub(r'[\W_]', '', s)
    rows = []
    for c in clips:
        if c['arm'] not in arms:
            continue
        ln, path = L[c['id']], os.path.join(HERE, c['file'])
        dur, pauses = internal_pauses(path)
        pause_flag = any(p > 1.2 for p in pauses) or len([p for p in pauses if p > 0.6]) > ln['n_sentences'] - 1
        tr = mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, language='ja')['text'].strip()
        latin = re.findall(r'[A-Za-z]{3,}', tr)
        src, hyp = norm(ln['jp']), norm(tr)
        blocks = [b for b in difflib.SequenceMatcher(None, src, hyp, autojunk=False).get_matching_blocks() if b.size >= 2]
        lead = blocks[0].b if blocks else len(hyp)
        rows.append({**{k: c[k] for k in ('id', 'role', 'emotion', 'arm', 'draw', 'file')}, 'dur': round(dur, 2),
                     'pauses': pauses, 'pause_flag': pause_flag, 'transcript': tr, 'latin': latin,
                     'lead_unmatched': lead, 'bleed_flag': bool(latin) or lead >= 4,
                     'lufs': loudness(path), 'peak_dbtp': true_peak(path), 'f0': median_f0(path), 'ms': c.get('ms')})
        r = rows[-1]
        print(f"{c['id']:<14} {c['arm']}{c['draw']} {dur:5.2f}s lufs {r['lufs']} pk {r['peak_dbtp']} "
              f"{'PAUSE ' if pause_flag else ''}{'BLEED ' if r['bleed_flag'] else ''}| {tr}")
    # loop: longer than 2x the median A duration of its line (A durations from screens_b2.json in Stage 3)
    base = rows if not stage3 else json.load(open(os.path.join(HERE, 'screens_b2.json'), encoding='utf-8'))['rows']
    a_med = {i: st.median(r['dur'] for r in base if r['id'] == i and r['arm'] == 'A') for i in {r['id'] for r in rows}}
    for r in rows:
        r['loop_flag'] = r['dur'] > 2 * a_med[r['id']]
    if stage3:
        C = [r for r in base if r['arm'] == 'C']
        out = {'rows': rows, 'verdict': verdict_s3(rows, C),
               'median_ms_P': st.median(r['ms'] for r in rows if r['ms']),
               'median_ms_A_paid_2b': st.median(c['ms'] for c in clips if c['arm'] == 'A' and c.get('ms'))}
        path = 'screens_s3.json'
    else:
        out = {'rows': rows, 'a_median_lufs': st.median(r['lufs'] for r in rows if r['arm'] == 'A'),
               'verdict': verdict_2b(rows)}
        path = 'screens_b2.json'
    print(json.dumps(out['verdict'], indent=1))
    json.dump(out, open(os.path.join(HERE, path), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def selftest():
    row = lambda arm, i=0, **k: {'id': f'x{i % 16}', 'arm': arm, 'lufs': -22.0, 'dur': 5.0, 'f0': 220.0,
                                 'peak_dbtp': -3.0, 'loop_flag': False, 'bleed_flag': False, 'pause_flag': False, **k}
    A = [row('A', i) for i in range(32)]
    assert verdict_2b(A + [row('C', i) for i in range(32)])['pass']
    v = verdict_2b(A + [row('C', i, peak_dbtp=-9.0) for i in range(32)])
    assert v['pass'] and v['median_plr_db (reported)'] == {'A': 19.0, 'C': 13.0}            # PLR is report-only
    assert verdict_2b(A + [row('C', i, lufs=-13.5) for i in range(32)])['fails'] == ['level']
    assert 'loop' in verdict_2b(A + [row('C', i, loop_flag=i < 2) for i in range(32)])['fails']
    assert verdict_2b(A + [row('C', i, bleed_flag=i < 4) for i in range(32)])['pass']        # A + 4 is allowed
    assert 'bleed' in verdict_2b(A + [row('C', i, bleed_flag=i < 5) for i in range(32)])['fails']
    C = [row('C', i) for i in range(16)] * 2
    P = [row('P', i) for i in range(8)]
    assert verdict_s3(P, C)['pass']
    assert not verdict_s3([row('P', i, lufs=-19.0) for i in range(8)], C)['checks']['level']
    assert not verdict_s3([row('P', i, f0=250.0) for i in range(8)], C)['checks']['pitch']
    assert not verdict_s3([row('P', i, loop_flag=i == 0) for i in range(8)], C)['pass']
    json.dumps(verdict_s3(P, C))
    print('screens_b2 selftest 10/10 OK')


if __name__ == '__main__':
    selftest() if 'selftest' in sys.argv else main('--stage3' in sys.argv)
