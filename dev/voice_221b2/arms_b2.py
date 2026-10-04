"""#221b Stage 2b arms and lines — the ONE place they are defined (PREREG_221b2.md).

Every arm starts from the SHIPPED request (arms_b.shipped_request: the real fish_tts() with requests.post
mocked), so text and params cannot drift from production. An arm changes only:
  A  = shipped as is (s2-pro, voice c4d8, no prosody)
  M  = model s2.1-pro-free, no prosody                       (Step 0 baseline only)
  C  = model s2.1-pro-free + "prosody": {"volume": V}          (the candidate; V fixed by Step 0)
  P  = model s2.1-pro      + "prosody": {"volume": V}          (Stage 3: the exact ship request)
"""
import contextlib, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'voice_221b'))
with contextlib.redirect_stdout(io.StringIO()):
    from arms_b import shipped_request, V221, AMADEUS      # noqa: E402
    from common import fs                                  # noqa: E402  (voice_221/common.py)
    from arms import tagged_text, sentences                # noqa: E402  (voice_221/arms.py)

AUDIO = os.path.join(AMADEUS, 'dev', 'voice_test', '221b2')   # git-ignored (.gitignore: dev/voice_test/)
os.makedirs(AUDIO, exist_ok=True)
LINES = os.path.join(HERE, 'lines_b2.json')
STEP0 = os.path.join(HERE, 'step0_result.json')     # Step 0 (FAILED 2026-10-01; kept as the record)
STEP0B = os.path.join(HERE, 'step0b_result.json')   # Step 0b (erratum 1; FAILED 2026-10-01; record only)
STEP0C = os.path.join(HERE, 'step0c_result.json')   # Step 0c (erratum 2) — the ONLY source of the prosody object

FREE, PAID = 's2.1-pro-free', 's2.1-pro'
V0 = -8.5                                  # PREREG: first volume tried in Step 0 (dB)
TARGET = ['t2', 't4', 't6', 't8', 'f2', 'f4', 'f6', 'f8']   # even lines, unheard in any new arm
GUARD_EMOTIONS = ['teasing', 'sarcastic', 'dismissive', 'curious']
STEP0_LINES = ['t2', 'f2']
STAGE3 = ['t2', 't6', 'f4', 'f8']          # + the first guard line of each emotion (g_<emotion>1)


def prosody():
    """The prosody object for C / P. Refuses unless Step 0c PASSED and its result file exists (PREREG erratum 2)."""
    if not os.path.exists(STEP0C):
        sys.exit('STOP: no step0c_result.json — no 2b / Stage 3 synthesis (PREREG_221b2 erratum 2)')
    r = json.load(open(STEP0C, encoding='utf-8'))
    if not r.get('passed'):
        sys.exit('STOP: Step 0c did not pass — no 2b / Stage 3 synthesis (PREREG_221b2 erratum 2)')
    return r['prosody']


def request_for(arm, emotion, jp, pros=None):
    """(payload, model header) for one clip. Text = shipped tag + Japanese, always.
    `pros` = the prosody object for C / P; a bare number means {"volume": n} (Step 0 / 0b)."""
    payload, headers = shipped_request(tagged_text('A', emotion, jp))
    if arm == 'A':
        return payload, headers['model']
    if arm == 'M':
        return payload, FREE
    if arm in ('C', 'P'):
        assert pros is not None
        pr = {'volume': pros} if isinstance(pros, (int, float)) else dict(pros)
        return {**payload, 'prosody': pr}, (FREE if arm == 'C' else PAID)
    raise ValueError(arm)


def load_lines():
    return {l['id']: l for l in json.load(open(LINES, encoding='utf-8'))['lines']}


if __name__ == '__main__':      # self-check: arms differ from shipped ONLY where intended
    if fs.FISH_MODEL != 's2-pro':
        sys.exit(print('arms_b2 self-check SKIPPED: arm A = the SHIPPED config, which #221b changed on 2026-10-04 '
                       f'(model {fs.FISH_MODEL}). The recorded results stand; to re-run: git checkout pre-221b.') or 0)
    L = load_lines()
    assert [i for i in L if i[0] in 'tf'] == TARGET and len(L) == 16
    ln = L['t2']
    pA, mA = request_for('A', ln['emotion'], ln['jp'])
    pM, mM = request_for('M', ln['emotion'], ln['jp'])
    pC, mC = request_for('C', ln['emotion'], ln['jp'], -8.5)
    pP, mP = request_for('P', ln['emotion'], ln['jp'], -8.5)
    assert mA == fs.FISH_MODEL == 's2-pro' and mM == mC == FREE and mP == PAID
    assert pA == pM and 'prosody' not in pA and 'speed' not in pA and pA['repetition_penalty'] == 1.2
    assert {k for k in pC if pC.get(k) != pA.get(k)} == {'prosody'} and pC['prosody'] == {'volume': -8.5}
    assert pC == pP and pA['reference_id'] == fs.FISH_VOICE_ID
    pN, _ = request_for('C', ln['emotion'], ln['jp'], {'normalize_loudness': False, 'volume': 3.5})
    assert {k for k in pN if pN.get(k) != pA.get(k)} == {'prosody'} and pN['prosody'] == {'normalize_loudness': False, 'volume': 3.5}
    assert pA['text'] == f"{fs.EMOTION_TAGS[ln['emotion']]} {ln['jp']}"
    print('arms_b2 self-check OK')
