"""#221b arms — the ONE place they are defined (PREREG_221b.md).

Every arm starts from the SHIPPED request, captured by calling the real kurisu_fish_server.fish_tts()
with requests.post mocked — so the text, params and headers cannot drift from production. An arm then
changes only the model header (M, MV) and the voice (MV).
"""
import contextlib, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
V221 = os.path.join(os.path.dirname(HERE), 'voice_221')
sys.path.insert(0, V221)
with contextlib.redirect_stdout(io.StringIO()):
    from common import fs, AMADEUS          # noqa: E402  (puts the repo root on sys.path)
    from arms import tagged_text            # noqa: E402  (#221: arm 'A' = shipped tag + Japanese)

AUDIO = os.path.join(AMADEUS, 'dev', 'voice_test', '221b')     # git-ignored (.gitignore: dev/voice_test/)
os.makedirs(AUDIO, exist_ok=True)

FREE_MODEL = 's2.1-pro-free'
FB03 = 'fb03cde57e7740c38a9601459afaae42'
ARMS = {                                  # arm -> (model header, reference_id); A = shipped as is
    'A':  (fs.FISH_MODEL, fs.FISH_VOICE_ID),
    'M':  (FREE_MODEL, fs.FISH_VOICE_ID),
    'MV': (FREE_MODEL, FB03),
}
PILOT = ['t1', 't3', 't5', 't7', 'f1', 'f3', 'f5', 'f7']      # odd-numbered frozen lines (PREREG)
NOISE = ['t1', 't5', 'f1', 'f5']                                # A1 vs A2 items


class _Captured(Exception):
    pass


def shipped_request(text):
    """(payload, headers) that the shipped fish_tts() would send for `text`. No network call."""
    box = {}
    def fake_post(url, headers=None, json=None, timeout=None):
        box.update(url=url, headers=dict(headers), payload=dict(json))
        raise _Captured
    orig = fs.requests.post
    fs.requests.post = fake_post
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fs.fish_tts(text)
    except _Captured:
        pass
    finally:
        fs.requests.post = orig
    assert box.get('url') == fs.FISH_API_URL, 'fish_tts did not reach requests.post'
    return box['payload'], box['headers']


def request_for(arm, emotion, jp):
    """(payload, model header) for one clip of `arm`. The text is always the shipped tag + Japanese."""
    payload, headers = shipped_request(tagged_text('A', emotion, jp))
    model, voice = ARMS[arm]
    payload = {**payload, 'reference_id': voice}
    return payload, model


def load_lines():
    L = json.load(open(os.path.join(V221, 'lines.json'), encoding='utf-8'))['lines']
    by = {l['id']: l for l in L}
    return [by[i] for i in PILOT]


if __name__ == '__main__':       # self-check: arms differ from shipped ONLY where intended
    ln = load_lines()[0]
    pA, mA = request_for('A', ln['emotion'], ln['jp'])
    pM, mM = request_for('M', ln['emotion'], ln['jp'])
    pV, mV = request_for('MV', ln['emotion'], ln['jp'])
    assert pA['text'] == f"{fs.EMOTION_TAGS[ln['emotion']]} {ln['jp']}"
    assert pA == pM and mA == 's2-pro' and mM == FREE_MODEL
    assert {k for k in pV if pV[k] != pA.get(k)} == {'reference_id'} and pV['reference_id'] == FB03
    assert 'speed' not in pA and 'prosody' not in pA and pA['repetition_penalty'] == 1.2
    assert len(load_lines()) == 8 and set(NOISE) <= set(PILOT)
    print('arms_b self-check OK')
