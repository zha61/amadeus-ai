#!/usr/bin/env python3
"""#221b2 Step 0c — is Fish's volume a SWITCH on loudness normalisation? (PREREG_221b2.md, ERRATUM 2). Free model only.

PROBE: 4 settings x t2, f2 x 2 draws = 16 clips.
  S1 {"volume": -1.0}                               does even a small value trigger the ~12.5 LU step?
  S2 {"volume": 3.0}                                does a POSITIVE value also trigger it?
  S3 {"normalize_loudness": false}                  is the step just normalisation switched off?
  S4 {"normalize_loudness": false, "volume": 3.5}   with normalisation off, is volume a DIAL?
SELECT (pure function `select`):
  a. a setting is a candidate if |median LUFS - (-22.0)| <= 1.5, max true peak <= -1.0 dBTP and its duration
     ratio vs M (Step 0's no-prosody clips) is in [0.92, 1.08]. Several -> the smallest error; a tie -> fewer fields.
  b. else, if S4 - S3 is within 3.5 +- 1.0 LU (the dial works once normalisation is off): build
     {"normalize_loudness": false, "volume": V}, V = -22.0 - median(S3), rounded to 0.5, clamped to [-10, +10].
  c. else STOP: no setting. Report the table and ask Zani.
CONFIRM: 6 FRESH clips (3 per line) of the selected setting. PASS if |median - (-22.0)| <= 1.0 LU, max true peak
  <= -1.0 dBTP, duration ratio vs M in [0.92, 1.08]. Pitch vs M on level-matched copies is REPORTED only.
  Fail -> STOP and ask Zani. No further step.
  python3 step0c.py [--dry | --rescore | selftest]
"""
import json, os, statistics as st, sys
from arms_b2 import HERE, AUDIO, STEP0C, STEP0_LINES, load_lines, request_for
from common import Guard, synth, loudness, duration, USD_PER_BYTE, MARGIN   # voice_221/common.py
from step0 import true_peak, TARGET_LUFS, CAP
from step0b import leveled_f0, confirm
from measure_b2 import median_f0

SETTINGS = {'S1': {'volume': -1.0}, 'S2': {'volume': 3.0}, 'S3': {'normalize_loudness': False},
            'S4': {'normalize_loudness': False, 'volume': 3.5}}
CLIPS = os.path.join(HERE, 'step0_clips.json')
COST = os.path.join(HERE, 'cost_b2.json')


def dur_ratio(M, C):
    return st.median(st.median(r['dur'] for r in C if r['id'] == i) / st.median(r['dur'] for r in M if r['id'] == i)
                     for i in STEP0_LINES)


def select(M, by):
    """by = {name: rows}. Returns (name, prosody, table) or (None, None, table). PREREG erratum 2."""
    table = {}
    for n, R in by.items():
        lu = st.median(r['lufs'] for r in R)
        table[n] = {'prosody': SETTINGS[n], 'median_lufs': lu, 'error_lu': round(lu - TARGET_LUFS, 2),
                    'max_true_peak': max(r['peak_dbtp'] for r in R), 'dur_ratio': round(dur_ratio(M, R), 3)}
        t = table[n]
        t['candidate'] = abs(t['error_lu']) <= 1.5 and t['max_true_peak'] <= -1.0 and 0.92 <= t['dur_ratio'] <= 1.08
    cands = sorted((n for n in table if table[n]['candidate']),
                   key=lambda n: (abs(table[n]['error_lu']), len(SETTINGS[n])))
    if cands:
        return cands[0], SETTINGS[cands[0]], table
    dial = table['S4']['median_lufs'] - table['S3']['median_lufs']
    table['dial_S4_minus_S3'] = round(dial, 2)
    if abs(dial - 3.5) <= 1.0:
        v = max(-10.0, min(10.0, round((TARGET_LUFS - table['S3']['median_lufs']) * 2) / 2))
        return 'dial', {'normalize_loudness': False, 'volume': v}, table
    return None, None, table


def confirm_rows(rows, pros):
    """The 6 FRESH Step 0c confirm clips of the selected prosody — and nothing else. (Bug 2026-10-01: a bare
    phase=='confirm' filter also pooled Step 0b's 6 confirm clips at volume 0.0, and reported a false FAIL.)"""
    return [r for r in rows if r.get('phase') == 'confirm' and r.get('setting') == 'confirm' and r.get('prosody') == pros]


def rescore():
    """Re-apply the PREREG confirm rule to the SAVED clips (no Fish call). Keeps the buggy result for the record."""
    res = json.load(open(STEP0C, encoding='utf-8'))
    bad = os.path.join(HERE, 'step0c_result_bug_pooled.json')
    if not os.path.exists(bad):
        json.dump(res, open(bad, 'w', encoding='utf-8'), indent=1)
    rows = json.load(open(CLIPS, encoding='utf-8'))
    M = [r for r in rows if r['arm'] == 'M']
    C = confirm_rows(rows, res['prosody'])
    assert len(C) == 6, f'expected 6 confirm clips, got {len(C)}'
    out = {k: v for k, v in res.items() if k in ('probe', 'selected', 'prosody', 'target_lufs')}
    out.update(confirm(M, C))
    out['rescored'] = 'confirm_rows() fix — the pooled Step 0b clips removed; see step0c_result_bug_pooled.json'
    json.dump(out, open(STEP0C, 'w', encoding='utf-8'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'probe'}, indent=1))
    print('Step 0c', 'PASSED' if out['passed'] else 'FAILED — stop and ask Zani (PREREG erratum 2)')


def main():
    L = load_lines()
    rows = json.load(open(CLIPS, encoding='utf-8'))
    one = st.mean(len(request_for('A', L[i]['emotion'], L[i]['jp'])[0]['text'].encode()) for i in STEP0_LINES)
    cost = json.load(open(COST))
    before = max(cost[k]['estimated_usd'] for k in ('step0', 'step0b'))   # each estimate is CUMULATIVE (Guard spent_before)
    print(f'Step 0c: 22 free calls; guard estimate ${22 * one * USD_PER_BYTE * MARGIN:.4f} + earlier ${before:.4f}; '
          f'shared cap ${CAP:.2f}')
    if '--dry' in sys.argv:
        return
    if os.path.exists(STEP0C):
        sys.exit(f'STOP: {STEP0C} exists — Step 0c already decided')
    guard = Guard(cap=CAP, spent_before=before)

    def run(name, pros, draws, phase):
        for d in range(1, draws + 1):
            for i in STEP0_LINES:
                if any(r.get('phase') == phase and r.get('setting') == name and r['id'] == i and r['draw'] == d for r in rows):
                    continue
                payload, model = request_for('C', L[i]['emotion'], L[i]['jp'], pros)
                path = os.path.join(AUDIO, f's0c_{phase}_{name}_{i}_{d}.mp3')
                sha = synth(payload['text'], path, guard=guard, payload_override=payload, model=model)
                if os.path.getsize(path) < 2000:
                    sys.exit(f'STOP: {path} is not audio')
                lu = loudness(path)
                rows.append({'id': i, 'arm': 'C', 'volume': pros.get('volume'), 'prosody': pros, 'setting': name,
                             'draw': d, 'phase': phase, 'model': model, 'file': os.path.relpath(path, HERE),
                             'sha256': sha, 'lufs': lu, 'peak_dbtp': true_peak(path), 'dur': round(duration(path), 3),
                             'f0': median_f0(path), 'f0_lev': leveled_f0(path, lu)})
                json.dump(rows, open(CLIPS, 'w', encoding='utf-8'), indent=1)
                print(f"  {phase} {name} {i} d{d}: {lu} LUFS, peak {rows[-1]['peak_dbtp']}")

    for n, p in SETTINGS.items():
        run(n, p, 2, 'probe')
    M = [r for r in rows if r['arm'] == 'M']
    by = {n: [r for r in rows if r.get('phase') == 'probe' and r.get('setting') == n] for n in SETTINGS}
    name, pros, table = select(M, by)
    print(json.dumps(table, indent=1))
    res = {'probe': table, 'selected': name, 'prosody': pros, 'target_lufs': TARGET_LUFS}
    if pros is None:
        res['passed'] = False
    else:
        print(f'selected {name}: {pros}')
        run('confirm', pros, 3, 'confirm')
        res.update(confirm(M, confirm_rows(rows, pros)))
    json.dump(res, open(STEP0C, 'w', encoding='utf-8'), indent=1)
    cost['step0c'] = guard.report()
    json.dump(cost, open(COST, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'probe'}, indent=1))
    print('Step 0c', 'PASSED' if res['passed'] else 'FAILED — stop and ask Zani (PREREG erratum 2)')


def selftest():
    M = [{'id': i, 'dur': 5.0} for i in STEP0_LINES] * 3
    mk = lambda lu, pk=-12.0, dur=5.0: [{'id': i, 'lufs': lu, 'peak_dbtp': pk, 'dur': dur} for i in STEP0_LINES] * 2
    # a. S3 lands at -22.6 -> chosen
    n, p, _ = select(M, {'S1': mk(-25.4), 'S2': mk(-25.4), 'S3': mk(-22.6), 'S4': mk(-19.1)})
    assert n == 'S3' and p == {'normalize_loudness': False}, (n, p)
    # b. none within 1.5, but the dial works -> V = -22 - (-25.5) = +3.5
    n, p, t = select(M, {'S1': mk(-25.4), 'S2': mk(-25.4), 'S3': mk(-25.5), 'S4': mk(-22.1 - 3.4 + 3.4)})
    assert n == 'S4', (n, t)                                 # S4 itself is within 1.5 -> plain candidate wins
    n, p, t = select(M, {'S1': mk(-25.4), 'S2': mk(-25.4), 'S3': mk(-27.0), 'S4': mk(-23.6)})
    assert n == 'dial' and p == {'normalize_loudness': False, 'volume': 5.0}, (n, p, t)
    # c. flat everywhere (the dial does nothing) -> STOP
    n, p, t = select(M, {'S1': mk(-25.4), 'S2': mk(-25.4), 'S3': mk(-25.5), 'S4': mk(-25.3)})
    assert n is None and p is None
    # d. a hot setting is not a candidate; a slow one neither
    n, _, _ = select(M, {'S1': mk(-22.0, pk=-0.5), 'S2': mk(-22.0, dur=5.6), 'S3': mk(-30.0), 'S4': mk(-30.0)})
    assert n is None
    # e. tie on error -> fewer fields (S3 over S4)
    n, _, _ = select(M, {'S1': mk(-30.0), 'S2': mk(-30.0), 'S3': mk(-22.5), 'S4': mk(-21.5)})
    assert n == 'S3'
    json.dumps(t)
    # f. MUTANT (the real bug): Step 0b's confirm rows share phase 'confirm' and must NOT be pooled
    pros = {'volume': -1.0}
    rows = [{'phase': 'confirm', 'volume': 0.0, 'id': 't2'}] * 6 + \
           [{'phase': 'confirm', 'setting': 'confirm', 'prosody': pros, 'id': 't2'}] * 6 + \
           [{'phase': 'confirm', 'setting': 'confirm', 'prosody': {'volume': 3.0}, 'id': 't2'}]
    assert len(confirm_rows(rows, pros)) == 6
    print('step0c selftest 7/7 OK')


if __name__ == '__main__':
    selftest() if 'selftest' in sys.argv else rescore() if '--rescore' in sys.argv else main()
