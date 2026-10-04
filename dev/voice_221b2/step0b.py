#!/usr/bin/env python3
"""#221b2 Step 0b — the amended loudness step (PREREG_221b2.md, ERRATUM 1). Free model only.

1. SELECT: C at -4.5 and -6.0 dB, 3 draws each on t2 and f2 (12 clips). A least-squares line through
   (V, median LUFS) for -8.5 (Step 0), -6.0 and -4.5 gives V* for -22.0 LUFS, rounded to 0.5 dB,
   clamped to [-8.5, 0].
2. CONFIRM: 6 FRESH C clips at V* (3 per line) — never the clips that chose V*.
   PASS if: |median LUFS - (-22.0)| <= 1.0; max true peak <= -1.0 dBTP; duration ratio vs M in [0.92, 1.08].
   Pitch vs M is REPORTED only, measured on copies level-matched to -14 LUFS.
Fail -> STOP and ask Zani. No further correction.
  python3 step0b.py [--dry | selftest]
"""
import json, math, os, statistics as st, subprocess, sys, tempfile
from arms_b2 import HERE, AUDIO, STEP0, STEP0B, STEP0_LINES, load_lines, request_for
from common import Guard, synth, loudness, duration, USD_PER_BYTE, MARGIN   # voice_221/common.py
from step0 import true_peak, TARGET_LUFS, CAP
from measure_b2 import median_f0

SELECT_V = (-6.0, -4.5)
DRAWS = 3
CLIPS = os.path.join(HERE, 'step0_clips.json')        # Step 0's file; Step 0b appends to it
COST = os.path.join(HERE, 'cost_b2.json')


def pick_volume(points):
    """points = [(V, median LUFS)] -> V* for TARGET_LUFS by least squares, rounded to 0.5, clamped."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    v = (TARGET_LUFS - a) / b
    return max(-8.5, min(0.0, round(v * 2) / 2)), round(a, 3), round(b, 3)


def leveled_f0(path, lufs, target=-14.0):
    d = tempfile.mkdtemp()
    dst = os.path.join(d, 'x.mp3')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-af', f'volume={target - lufs:.2f}dB', '-b:a', '192k', dst],
                   check=True)
    return median_f0(dst)


def confirm(M, C):
    """PREREG Erratum 1 confirmation rules. Pure function (selftest)."""
    mC = st.median(r['lufs'] for r in C)
    dur = st.median(st.median(r['dur'] for r in C if r['id'] == i) / st.median(r['dur'] for r in M if r['id'] == i)
                    for i in STEP0_LINES)
    semi = st.median(12 * math.log2(st.median(r['f0_lev'] for r in C if r['id'] == i and r['f0_lev']) /
                                    st.median(r['f0_lev'] for r in M if r['id'] == i and r['f0_lev'])) for i in STEP0_LINES)
    checks = {'level': abs(mC - TARGET_LUFS) <= 1.0, 'peak': max(r['peak_dbtp'] for r in C) <= -1.0,
              'duration': 0.92 <= dur <= 1.08}
    return {'median_lufs_C': mC, 'level_error_lu': round(mC - TARGET_LUFS, 2),
            'max_true_peak_C': max(r['peak_dbtp'] for r in C), 'dur_ratio_C_vs_M': round(dur, 3),
            'pitch_semitones_C_vs_M_leveled (reported only)': round(semi, 2), 'checks': checks,
            'passed': all(checks.values())}


def main():
    L = load_lines()
    rows = json.load(open(CLIPS, encoding='utf-8'))
    one = st.mean(len(request_for('A', L[i]['emotion'], L[i]['jp'])[0]['text'].encode()) for i in STEP0_LINES)
    est = 18 * one * USD_PER_BYTE * MARGIN
    cost = json.load(open(COST))
    before = cost['step0']['estimated_usd']
    print(f'Step 0b: 18 free calls; guard estimate ${est:.4f} + earlier ${before:.4f}; shared cap ${CAP:.2f}')
    if '--dry' in sys.argv:
        return
    if os.path.exists(STEP0B):
        sys.exit(f'STOP: {STEP0B} exists — Step 0b already decided')
    guard = Guard(cap=CAP, spent_before=before)

    def run(vol, tag):
        for d in range(1, DRAWS + 1):
            for i in STEP0_LINES:
                if any(r['id'] == i and r['arm'] == 'C' and r['volume'] == vol and r['draw'] == d and r.get('phase') == tag
                       for r in rows):
                    continue
                payload, model = request_for('C', L[i]['emotion'], L[i]['jp'], vol)
                path = os.path.join(AUDIO, f's0b_{tag}_{i}_C{vol}_{d}.mp3')
                sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
                if os.path.getsize(path) < 2000:
                    sys.exit(f'STOP: {path} is not audio')
                lu = loudness(path)
                rows.append({'id': i, 'arm': 'C', 'volume': vol, 'draw': d, 'phase': tag, 'model': model,
                             'file': os.path.relpath(path, HERE), 'sha256': sha, 'lufs': lu,
                             'peak_dbtp': true_peak(path), 'dur': round(duration(path), 3),
                             'f0': median_f0(path), 'f0_lev': leveled_f0(path, lu)})
                json.dump(rows, open(CLIPS, 'w', encoding='utf-8'), indent=1)
                print(f"  {tag} {i} vol={vol} d{d}: {lu} LUFS, peak {rows[-1]['peak_dbtp']}")

    for v in SELECT_V:
        run(v, 'select')
    s0 = json.load(open(STEP0))
    pts = [(-8.5, s0['median_lufs_C'])] + [(v, st.median(r['lufs'] for r in rows if r.get('phase') == 'select'
                                                        and r['volume'] == v)) for v in SELECT_V]
    vstar, a, b = pick_volume(pts)
    print(f'select points {pts} -> line a={a} b={b} -> V* = {vstar}')
    run(vstar, 'confirm')
    M = [r for r in rows if r['arm'] == 'M']
    for r in M:
        if 'f0_lev' not in r:
            r['f0_lev'] = leveled_f0(os.path.join(HERE, r['file']), r['lufs'])
    json.dump(rows, open(CLIPS, 'w', encoding='utf-8'), indent=1)
    C = [r for r in rows if r.get('phase') == 'confirm' and r['volume'] == vstar]
    res = {'volume': vstar, 'select_points': pts, 'fit': {'a': a, 'b': b}, 'target_lufs': TARGET_LUFS,
           **confirm(M, C)}
    json.dump(res, open(STEP0B, 'w', encoding='utf-8'), indent=1)
    cost['step0b'] = guard.report()
    json.dump(cost, open(COST, 'w'), indent=1)
    print(json.dumps(res, indent=1))
    print('Step 0b', 'PASSED' if res['passed'] else 'FAILED — stop and ask Zani (PREREG erratum 1)')


def selftest():
    v, a, b = pick_volume([(-8.5, -25.9), (-6.0, -23.4), (-4.5, -21.9)])      # exactly linear, slope 1
    assert v == -4.5, (v, a, b)
    assert pick_volume([(-8.5, -25.9), (-6.0, -24.0), (-4.5, -22.6)])[0] == -3.5
    assert pick_volume([(-8.5, -40.0), (-6.0, -39.0), (-4.5, -38.0)])[0] == 0.0           # clamped high
    assert pick_volume([(-8.5, -10.0), (-6.0, -8.0), (-4.5, -6.0)])[0] == -8.5             # clamped low
    mk = lambda arm, lu, dur=5.0, pk=-12.0, f=220.0: [{'id': i, 'arm': arm, 'lufs': lu, 'dur': dur, 'peak_dbtp': pk,
                                                       'f0_lev': f} for i in STEP0_LINES] * 3
    M = mk('M', -13.0)
    assert confirm(M, mk('C', -22.4))['passed']
    assert not confirm(M, mk('C', -23.2))['checks']['level']
    assert not confirm(M, mk('C', -22.0, pk=-0.5))['checks']['peak']
    assert not confirm(M, mk('C', -22.0, dur=5.6))['checks']['duration']
    assert confirm(M, mk('C', -22.0, f=260.0))['passed']                                  # pitch is report-only now
    print('step0b selftest 9/9 OK')


if __name__ == '__main__':
    selftest() if 'selftest' in sys.argv else main()
