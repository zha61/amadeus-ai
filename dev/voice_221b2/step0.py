#!/usr/bin/env python3
"""#221b2 Step 0 — does "prosody": {"volume": V} bring s2.1 down to s2-pro's level? (PREREG_221b2.md)

Free model only. Lines t2 f2, 3 draws each of M (no prosody) and C (volume V0), interleaved.
One correction is allowed (V1), then 6 more C clips. Writes step0_clips.json and step0_result.json.
  python3 step0.py --dry     cost estimate only, nothing sent
  python3 step0.py           synthesis + decision
"""
import json, os, statistics as st, subprocess, sys
from arms_b2 import HERE, AUDIO, STEP0, V0, STEP0_LINES, load_lines, request_for
from common import Guard, synth, loudness, duration, USD_PER_BYTE, MARGIN   # voice_221/common.py
from measure_b2 import median_f0

TARGET_LUFS = -22.0          # median of the 16 s2-pro A clips (voice_221b/screens_b.json summary.A)
CAP = 0.55                   # shared with synth_b2.py (Step 0 + 2b), every call counted as paid x1.5
DRAWS = 3
CLIPS = os.path.join(HERE, 'step0_clips.json')
COST = os.path.join(HERE, 'cost_b2.json')


def true_peak(path):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    vals = [l for l in err.splitlines() if 'Peak:' in l and 'dBFS' in l]
    return float(vals[-1].split()[1]) if vals else None


def measure(path):
    return {'lufs': loudness(path), 'peak_dbtp': true_peak(path), 'dur': round(duration(path), 3),
            'f0': median_f0(path)}


def decide(rows, vol):
    """PREREG Step 0 rules on the M rows and the C rows made at `vol`. Pure function (selftest)."""
    M = [r for r in rows if r['arm'] == 'M']
    C = [r for r in rows if r['arm'] == 'C' and r['volume'] == vol]
    mM, mC = st.median(r['lufs'] for r in M), st.median(r['lufs'] for r in C)
    dur = st.median(st.median(r['dur'] for r in C if r['id'] == i) / st.median(r['dur'] for r in M if r['id'] == i)
                    for i in STEP0_LINES)
    import math
    semi = st.median(12 * math.log2(st.median(r['f0'] for r in C if r['id'] == i and r['f0']) /
                                    st.median(r['f0'] for r in M if r['id'] == i and r['f0'])) for i in STEP0_LINES)
    peak = max(r['peak_dbtp'] for r in C)
    out = {'volume': vol, 'median_lufs_M': mM, 'median_lufs_C': mC, 'effect_lu': round(mM - mC, 2),
           'level_error_lu': round(mC - TARGET_LUFS, 2), 'max_true_peak_C': peak,
           'dur_ratio_C_vs_M': round(dur, 3), 'pitch_semitones_C_vs_M': round(semi, 2)}
    out['acts'] = out['effect_lu'] >= 5.0
    out['checks'] = {'level': abs(out['level_error_lu']) <= 1.0, 'peak': peak <= -1.0,
                     'duration': 0.92 <= dur <= 1.08, 'pitch': abs(semi) <= 1.0}
    out['passed'] = out['acts'] and all(out['checks'].values())
    return out


def may_correct(res):
    """A correction is allowed ONLY when volume acts, the level misses, and every other check passes."""
    return res['acts'] and not res['checks']['level'] and all(v for k, v in res['checks'].items() if k != 'level')


def corrected(res):
    """The one allowed correction: V1 = V0 - level error, rounded to 0.5 dB."""
    return round((res['volume'] - res['level_error_lu']) * 2) / 2


def main():
    L = load_lines()
    rows = json.load(open(CLIPS, encoding='utf-8')) if os.path.exists(CLIPS) else []
    have = {(r['id'], r['arm'], r['volume'], r['draw']) for r in rows}
    todo = [(i, arm, V0 if arm == 'C' else None, d) for d in range(1, DRAWS + 1) for i in STEP0_LINES for arm in ('M', 'C')]
    worst = sum(len(request_for('A', L[i]['emotion'], L[i]['jp'])[0]['text'].encode()) for i, *_ in todo) * 1.5
    print(f'Step 0: {len(todo)} free calls (+ up to 6 after one correction); guard estimate '
          f'${worst * USD_PER_BYTE * MARGIN:.4f} if every call were billed; shared cap ${CAP:.2f}')
    if '--dry' in sys.argv:
        return
    if os.path.exists(STEP0):
        sys.exit(f'STOP: {STEP0} exists — Step 0 already decided')
    guard = Guard(cap=CAP)

    def run(items):
        for i, arm, vol, d in items:
            if (i, arm, vol, d) in have:
                continue
            payload, model = request_for(arm, L[i]['emotion'], L[i]['jp'], vol)
            path = os.path.join(AUDIO, f"s0_{i}_{arm}{'' if vol is None else vol}_{d}.mp3")
            sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
            if os.path.getsize(path) < 2000:
                sys.exit(f'STOP: {path} is not audio')
            rows.append({'id': i, 'arm': arm, 'volume': vol, 'draw': d, 'model': model,
                         'file': os.path.relpath(path, HERE), 'sha256': sha, **measure(path)})
            json.dump(rows, open(CLIPS, 'w', encoding='utf-8'), indent=1)
            print(f"  {i} {arm} vol={vol} d{d}: {rows[-1]['lufs']} LUFS, peak {rows[-1]['peak_dbtp']}")

    run(todo)
    res = decide(rows, V0)
    tries = [res]
    if may_correct(res):
        v1 = corrected(res)
        print(f'Step 0: V0={V0} failed {res["checks"]}; one correction V1={v1}')
        run([(i, 'C', v1, d) for d in range(1, DRAWS + 1) for i in STEP0_LINES])
        res = decide(rows, v1)
        tries.append(res)
    final = {**res, 'tries': tries, 'target_lufs': TARGET_LUFS}
    json.dump(final, open(STEP0, 'w', encoding='utf-8'), indent=1)
    json.dump({'step0': guard.report()}, open(COST, 'w'), indent=1)
    print(json.dumps(final, indent=1))
    print('Step 0', 'PASSED' if final['passed'] else 'FAILED — stop and ask Zani (PREREG)')


def selftest():
    mk = lambda arm, vol, lufs, f0=220.0, dur=5.0, pk=-3.0: [
        {'id': i, 'arm': arm, 'volume': vol, 'lufs': lufs, 'f0': f0, 'dur': dur, 'peak_dbtp': pk} for i in STEP0_LINES]
    base = mk('M', None, -13.5) * 3
    r = decide(base + mk('C', -8.5, -22.3) * 3, -8.5)
    assert r['passed'] and r['acts'], r
    r = decide(base + mk('C', -8.5, -13.4) * 3, -8.5)            # volume ignored
    assert not r['acts'] and not r['passed'], r
    r = decide(base + mk('C', -8.5, -19.0) * 3, -8.5)            # acts, misses the level
    assert r['acts'] and not r['checks']['level'] and may_correct(r) and corrected(r) == -11.5, (r, corrected(r))
    r = decide(base + mk('C', -8.5, -19.0, f0=250.0) * 3, -8.5)  # level AND pitch fail -> no correction
    assert not may_correct(r)
    r = decide(base + mk('C', -8.5, -13.4) * 3, -8.5)
    assert not may_correct(r)                                    # volume ignored -> stop, no correction
    r = decide(base + mk('C', -8.5, -22.0, f0=250.0) * 3, -8.5)  # pitch moved 2.2 semitones
    assert not r['checks']['pitch'] and not r['passed']
    r = decide(base + mk('C', -8.5, -22.0, dur=5.6) * 3, -8.5)   # 12% slower
    assert not r['checks']['duration']
    r = decide(base + mk('C', -8.5, -22.0, pk=-0.5) * 3, -8.5)   # too hot
    assert not r['checks']['peak']
    json.dumps(r)
    print('step0 selftest 8/8 OK')


if __name__ == '__main__':
    selftest() if 'selftest' in sys.argv else main()
