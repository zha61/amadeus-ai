"""
dev/whisper_server_test.py — /transcribe returns Whisper's per-segment compression ratio
(backlog #205 / bugs.md 97).  Run:  /opt/homebrew/bin/python3 dev/whisper_server_test.py

mlx_whisper is replaced with a stub BEFORE the server is imported, so no model and no MLX/Metal
load. The shipped route runs through Flask's test client. Exit 0 = pass, 1 = fail.
"""
import io
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
stub = types.ModuleType('mlx_whisper')
stub.result = {}
stub.transcribe = lambda *a, **k: stub.result
sys.modules['mlx_whisper'] = stub
import kurisu_whisper_server as srv  # noqa: E402

srv.model_ready.set()
client = srv.app.test_client()
fails = 0


def post(result):
    stub.result = result
    r = client.post('/transcribe', data={'audio': (io.BytesIO(b'RIFF'), 'utterance.wav')},
                    content_type='multipart/form-data')
    return r.status_code, r.get_json()


def check(name, cond):
    global fails
    print(('  ok   ' if cond else '  FAIL ') + name)
    fails += 0 if cond else 1


seg = lambda cr, ns=0.05, lp=-0.3: {'compression_ratio': cr, 'no_speech_prob': ns, 'avg_logprob': lp}
code, j = post({'text': ' What a great deal, a great deal', 'segments': [seg(1.1), seg(3.08), seg(1.4)]})
check('200 and compression_ratio = the MAXIMUM over segments (3.08)', code == 200 and j['compression_ratio'] == 3.08)
check('the existing fields are unchanged', j['no_speech_prob'] == 0.05 and j['avg_logprob'] == -0.3
      and j['transcript'] == 'What a great deal, a great deal')
code, j = post({'text': '', 'segments': []})
check('0 segments: no crash, compression_ratio 0.0, no_speech 1.0', code == 200 and j['compression_ratio'] == 0.0
      and j['no_speech_prob'] == 1.0)
code, j = post({'text': 'hi', 'segments': [{'no_speech_prob': 0.1, 'avg_logprob': -0.2}]})
check('a segment without compression_ratio: no crash, 0.0', code == 200 and j['compression_ratio'] == 0.0)

print(f'\n{4 - fails}/4 checks passed')
sys.exit(1 if fails else 0)
