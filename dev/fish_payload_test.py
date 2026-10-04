#!/usr/bin/env python3
"""Backlog #225 + #221b — the payload /speak sends to Fish. No network, no Fish credit, no gemma4.

Drives the SHIPPED /speak route (Flask test client) with translation and requests.post mocked,
and checks the OUTCOME: the exact JSON body Fish receives.
  1. /speak answers with audio, and the body is exactly the V3 payload (plus text and voice id).
  2. No "speed" anywhere: she speaks at Fish's default 1.0 (Zani, 2026-09-30). Fish reads speed only from
     prosody.speed; a top-level "speed" was sent and ignored for months.
  2b. #221b (2026-10-04): model header "s2.1-pro" and prosody EXACTLY {"volume": -1.0}. Fish's volume is a switch
     (0/absent = loud path): a missing or zero volume makes her ~10 LU louder (CLAUDE.md 54, bugs.md 99).
  3. repetition_penalty is 1.2, never 1.1 (bugs.md 54, phoneme loop).
  4. The text is the emotion tag + the Japanese, and the log has no false "Speed:" line.
Mutants: the same checker must REJECT a top-level speed, a prosody.speed, repetition_penalty 1.1, no prosody,
volume 0, normalize_loudness in prosody, and the old model header s2-pro.
Usage: python3 dev/fish_payload_test.py   (exit 0 = all pass)
"""
import contextlib, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with contextlib.redirect_stdout(io.StringIO()):
    import kurisu_fish_server as fs

EXPECTED = {"reference_id": fs.FISH_VOICE_ID, "format": "mp3", "mp3_bitrate": 128, "latency": "normal",
            "normalize": True, "chunk_length": 200, "temperature": 0.7, "top_p": 0.8,
            "repetition_penalty": 1.2, "prosody": {"volume": -1.0}}
MODEL = 's2.1-pro'          # literal on purpose: comparing with fs.FISH_MODEL would test nothing
JP = 'べ、別に。心配なんかしてないから。'


def problems(body, text):
    """Everything wrong with one request body. Empty list = correct."""
    out = []
    if body.get('text') != text:
        out.append(f'text {body.get("text")!r} != {text!r}')
    if 'speed' in body:
        out.append('top-level "speed" is sent (Fish ignores it; backlog #225)')
    if body.get('prosody') != {'volume': -1.0}:
        out.append(f'prosody {body.get("prosody")!r} != {{"volume": -1.0}} (loudness switch, bugs.md 99)')
    rest = {k: v for k, v in body.items() if k != 'text'}
    if rest != EXPECTED:
        out.append(f'payload differs from the shipped config: {rest}')
    return out


def header_problems(headers):
    return [] if (headers or {}).get('model') == MODEL else [f'model header {(headers or {}).get("model")!r} != {MODEL!r}']


class _Resp:
    status_code = 200
    content = b'ID3fake-mp3'
    def raise_for_status(self):
        pass


def run_speak(emotion):
    sent = {}
    def fake_post(url, headers=None, json=None, timeout=None):
        sent['url'], sent['body'], sent['headers'] = url, json, headers
        return _Resp()
    orig_post, orig_tr = fs.requests.post, fs.translate_to_japanese
    fs.requests.post, fs.translate_to_japanese = fake_post, (lambda text: JP)
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            r = fs.app.test_client().post('/speak', json={'text': 'N-not that I was worried.', 'emotion': emotion})
    finally:
        fs.requests.post, fs.translate_to_japanese = orig_post, orig_tr
    return r, sent, log.getvalue()


passed = failed = 0
def check(name, ok, detail=''):
    global passed, failed
    if ok:
        passed += 1
        print(f'  ok   {name}')
    else:
        failed += 1
        print(f'  FAIL {name} {detail}')


for emo in ('tsundere', 'flustered', 'default'):
    r, sent, log = run_speak(emo)
    text = f'{fs.EMOTION_TAGS[emo]} {JP}'
    check(f'{emo}: /speak returns audio', r.status_code == 200 and bool(r.get_json().get('audio_b64')), r.status_code)
    check(f'{emo}: Fish URL and model header s2.1-pro', sent.get('url') == fs.FISH_API_URL
          and not header_problems(sent.get('headers')), sent.get('headers', {}).get('model'))
    p = problems(sent.get('body', {}), text)
    check(f'{emo}: body is the shipped payload, no speed, prosody = volume -1.0 only', not p, p)
    check(f'{emo}: no false "Speed:" log line', 'Speed:' not in log)

print('mutants (each must be REJECTED by the checker):')
good = {**EXPECTED, 'text': 'x'}
for name, mut in (('top-level speed 1.1', {**good, 'speed': 1.1}),
                  ('prosody.speed 1.1', {**good, 'prosody': {'speed': 1.1}}),
                  ('repetition_penalty 1.1 (bugs.md 54)', {**good, 'repetition_penalty': 1.1}),
                  ('no prosody (loud path)', {k: v for k, v in good.items() if k != 'prosody'}),
                  ('volume 0 (loud path)', {**good, 'prosody': {'volume': 0}}),
                  ('prosody.speed added', {**good, 'prosody': {'volume': -1.0, 'speed': 1.0}}),
                  ('normalize_loudness added', {**good, 'prosody': {'volume': -1.0, 'normalize_loudness': False}})):
    check(f'mutant caught: {name}', bool(problems(mut, 'x')))
check('mutant caught: model header s2-pro', bool(header_problems({'model': 's2-pro'})))
check('control: the correct body passes', not problems(good, 'x'))

print(f'\nfish_payload_test: {passed} passed, {failed} failed')
sys.exit(1 if failed else 0)
