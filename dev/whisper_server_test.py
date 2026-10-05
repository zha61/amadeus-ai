"""
dev/whisper_server_test.py — /transcribe returns Whisper's per-segment compression ratio
(backlog #205 / bugs.md 97), and the model loads on FIRST USE and unloads when idle (backlog #226).
Run:  /opt/homebrew/bin/python3 dev/whisper_server_test.py [--mutants]
--mutants runs the same checks against 4 broken copies of the server; each must FAIL.

mlx_whisper is replaced with a stub BEFORE the server is imported, so no model and no MLX/Metal
load. The shipped route runs through Flask's test client. Exit 0 = pass, 1 = fail.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRV_DIR = os.environ.get('WHISPER_SRV_DIR', ROOT)   # a mutant copy, when --mutants runs
SRC = os.path.join(ROOT, 'kurisu_whisper_server.py')
MUTANTS = [   # (name, exact text in the server, replacement) — each must make a check FAIL
    ('unload bypasses the MLX worker', "    return _mlx.submit(_idle_job).result()", "    return _idle_job()"),
    ('/transcribe bypasses the MLX worker', "        result, was_loaded, t0 = _mlx.submit(job).result()",
     "        result, was_loaded, t0 = job()"),
    ('unload ignores idle time', "if model_loaded() and time.time() - _last_use >= IDLE_UNLOAD_S:",
     "if model_loaded():"),
    ('loads by name, not the local folder', "transcribe(tmp_path, path_or_hf_repo=model_path",
     "transcribe(tmp_path, path_or_hf_repo=MODEL"),
    ('unload keeps the model', "    h.model = None\n", ""),
    ('/warm does not load', "        _model_holder().get_model(model_path, mx.float16)", "        pass"),
    ('/warm bypasses the MLX worker', "    status = _mlx.submit(_warm_job).result()", "    status = _warm_job()"),
    ('/warm loads with another dtype', "get_model(model_path, mx.float16)", "get_model(model_path, 'float32')"),
    ('boot warm-up restored', "    threading.Thread(target=_ensure_files, daemon=True).start()",
     "    threading.Thread(target=_ensure_files, daemon=True).start()\n"
     "    threading.Thread(target=lambda: mlx_whisper.transcribe('x.wav', path_or_hf_repo=model_path), daemon=True).start()"),
]

if '--mutants' in sys.argv:
    src, bad = open(SRC).read(), 0
    for name, old, new in MUTANTS:
        if src.count(old) != 1:
            print(f'  MUTANT NOT APPLIED (text not found once): {name}'); bad += 1; continue
        d = tempfile.mkdtemp()
        open(os.path.join(d, 'kurisu_whisper_server.py'), 'w').write(src.replace(old, new))
        r = subprocess.run([sys.executable, os.path.abspath(__file__)], env={**os.environ, 'WHISPER_SRV_DIR': d},
                           capture_output=True, text=True, timeout=60)
        shutil.rmtree(d)
        caught = r.returncode != 0
        bad += not caught
        print(f'  {"caught " if caught else "MISSED "} {name}')
    print(f'\n{len(MUTANTS) - bad}/{len(MUTANTS)} mutants caught')
    sys.exit(1 if bad else 0)

sys.path.insert(0, SRV_DIR)


MLX_THREADS = set()   # every thread that touched the (stub) model — MLX streams are per-thread


class ModelHolder:
    model = None
    model_path = None
    get_calls = []

    @classmethod
    def get_model(cls, path, dtype):   # mirrors mlx_whisper's: load only if absent or path differs
        cls.get_calls.append((path, dtype))
        MLX_THREADS.add(threading.current_thread().name)
        if cls.model is None or path != cls.model_path:
            cls.model, cls.model_path = object(), path
            stub.loads += 1
        return cls.model


stub = types.ModuleType('mlx_whisper')
stub.result = {}
stub.loads = 0
stub.paths = []
stub.during = None          # optional hook run INSIDE a transcription


def _stub_transcribe(path, path_or_hf_repo=None, **k):
    stub.paths.append(path_or_hf_repo)
    ModelHolder.get_model(path_or_hf_repo, 'float16')   # transcribe() loads through the same holder
    if stub.during:
        stub.during()
    return stub.result


stub.transcribe = _stub_transcribe
sub_t = types.ModuleType('mlx_whisper.transcribe')
sub_t.ModelHolder = ModelHolder
mx = types.ModuleType('mlx.core')
mx.cleared = 0


def _clear():
    mx.cleared += 1
    MLX_THREADS.add(threading.current_thread().name)


mx.clear_cache = _clear
mx.float16 = 'float16'
sys.modules.update({'mlx_whisper': stub, 'mlx_whisper.transcribe': sub_t, 'mlx': types.ModuleType('mlx'),
                    'mlx.core': mx})
import kurisu_whisper_server as srv  # noqa: E402

LOADS_AT_IMPORT = stub.loads
_src = open(os.path.join(SRV_DIR, 'kurisu_whisper_server.py')).read()
MAIN_BLOCK = _src[_src.index("if __name__ == '__main__':"):]
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

# ── backlog #226: load on first use, unload when idle ──────────────────────────────────
check('#226 importing the server loads no model', LOADS_AT_IMPORT == 0)
check('#226 the start-up block runs no transcription (no boot warm-up)', 'transcribe(' not in MAIN_BLOCK
      and '_warmup' not in MAIN_BLOCK and '_ensure_files' in MAIN_BLOCK)
ModelHolder.model = None; stub.loads = 0; stub.paths.clear(); mx.cleared = 0
srv.model_path = '/LOCAL/SNAPSHOT'
check('#226 nothing is loaded before the first /transcribe', not srv.model_loaded()
      and srv.app.test_client().get('/health').get_json()['model_loaded'] is False)
post({'text': 'hi', 'segments': []}); post({'text': 'hi', 'segments': []})
check('#226 the first call loads ONCE; the second reuses it', stub.loads == 1 and srv.model_loaded())
check('#226 the model loads from the LOCAL folder (offline-safe reloads)', set(stub.paths) == {'/LOCAL/SNAPSHOT'})
check('#226 /health reports model_loaded', srv.app.test_client().get('/health').get_json()['model_loaded'] is True)
check('#226 no unload while used recently', srv._idle_check() is False and srv.model_loaded())
srv._last_use = time.time() - srv.IDLE_UNLOAD_S - 1
check('#226 idle -> unloaded and the MLX cache cleared', srv._idle_check() is True and not srv.model_loaded()
      and mx.cleared == 1)
post({'text': 'hi', 'segments': []})
check('#226 a call after an unload reloads', stub.loads == 2 and srv.model_loaded())
# An unload attempted DURING a transcription must wait for it, and must then see the fresh use.
srv._last_use = time.time() - srv.IDLE_UNLOAD_S - 1
seen = {}


def _during():
    t = threading.Thread(target=lambda: seen.setdefault('unloaded', srv._idle_check()))
    t.start(); time.sleep(0.3)
    seen['blocked'] = t.is_alive(); seen['loaded_mid'] = srv.model_loaded(); seen['t'] = t


stub.during = _during
post({'text': 'hi', 'segments': []})
stub.during = None
seen['t'].join(5)
check('#226 an unload never runs during a transcription (it waits, then sees the fresh use)',
      seen['blocked'] and seen['loaded_mid'] and seen.get('unloaded') is False and srv.model_loaded())

# ── backlog #226b: /warm loads the model when the mic opens ─────────────────────────────
ModelHolder.model = None; stub.loads = 0
srv._last_use = 0.0
w = srv.app.test_client().post('/warm').get_json()
check('#226b /warm loads an unloaded model once and reports it', w['status'] == 'loaded' and stub.loads == 1
      and srv.model_loaded() and time.time() - srv._last_use < 5)
srv._last_use = 0.0
w = srv.app.test_client().post('/warm').get_json()
check('#226b /warm on a loaded model: no second load, idle clock renewed', w['status'] == 'already-loaded'
      and stub.loads == 1 and time.time() - srv._last_use < 5)
post({'text': 'hi', 'segments': []})
check('#226b a transcription after /warm does not load again', stub.loads == 1)
ModelHolder.get_calls.clear(); ModelHolder.model = None; stub.paths.clear()
srv.app.test_client().post('/warm')
check('#226b ALL model work (load, transcribe, prewarm, unload) ran on ONE worker thread',
      len(MLX_THREADS) == 1 and next(iter(MLX_THREADS)).startswith('mlx'))
check('#226b /warm loads with EXACTLY transcribe()\'s arguments (local folder, float16) and decodes nothing',
      ModelHolder.get_calls == [('/LOCAL/SNAPSHOT', 'float16')] and stub.paths == [])

total = 19
print(f'\n{total - fails}/{total} checks passed')
sys.exit(1 if fails else 0)
