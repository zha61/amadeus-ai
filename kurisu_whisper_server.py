import os
# Ensure Homebrew binaries (ffmpeg etc.) are findable — Electron doesn't inherit
# the full shell PATH, same issue as PYTHON/OLLAMA hardcoded paths (bugs 10, 19, 27).
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

from flask import Flask, request, jsonify
import mlx_whisper
import gc
from concurrent.futures import ThreadPoolExecutor
import tempfile
import threading
import time

app = Flask(__name__)

# large-v3-turbo (809M): accuracy within ~0.4pt WER of full large-v3 — clearly
# better than the previous whisper-medium — at ~4x realtime on Apple Silicon,
# in the same ~1.5GB memory class. 2026 consensus pick for local Mac STT.
# Swapped July 18, 2026 after download + functional verification; medium deleted.
MODEL = 'mlx-community/whisper-large-v3-turbo'
model_ready = threading.Event()   # the model FILES are on disk (not: the model is in memory)
model_path = MODEL                # replaced by the local snapshot folder once it is known

# Backlog #226 (2026-10-04): the model is loaded on the FIRST /transcribe and unloaded after
# IDLE_UNLOAD_S with no transcription. It used to load at boot and hold 2.45 GiB all session,
# while Zani mostly types. Measured (app closed): load adds ~0.3-0.5 s once; unload frees
# 2.08 GiB (2.28 -> 0.20). 10 min = HF_IDLE_MAX_MS in amadeus.html, so a live hands-free
# session never loses its model.
# #226b: ALL MLX work (load, transcribe, prewarm, unload) runs on ONE worker thread. MLX streams
# belong to the thread that created them: a model loaded by ModelHolder.get_model() in one Flask
# request thread made a transcription in another thread fail with "There is no Stream(gpu, 1) in
# current thread" (measured 2026-10-04). The single worker also serialises every model change,
# so an unload can never run during a transcription.
IDLE_UNLOAD_S = 600
_mlx = ThreadPoolExecutor(max_workers=1, thread_name_prefix='mlx')
_last_use = 0.0


def _model_holder():
    from mlx_whisper.transcribe import ModelHolder
    return ModelHolder


def model_loaded():
    return _model_holder().model is not None


def _unload(reason):
    """Runs on the _mlx worker only."""
    if not model_loaded():
        return False
    h = _model_holder()
    h.model = None
    h.model_path = None
    gc.collect()
    try:
        import mlx.core as mx
        mx.clear_cache()            # returns MLX's cached Metal buffers to the system
    except Exception as e:
        print(f'[whisper] clear_cache failed: {e}')
    print(f'[whisper] Model unloaded ({reason})', flush=True)
    return True


def _idle_job():
    if model_loaded() and time.time() - _last_use >= IDLE_UNLOAD_S:
        return _unload(f'idle {int(time.time() - _last_use)}s')
    return False


def _idle_check():
    return _mlx.submit(_idle_job).result()


def _idle_unloader():
    while True:
        time.sleep(30)
        try:
            _idle_check()
        except Exception as e:
            print(f'[whisper] idle check failed: {e}', flush=True)


def _ensure_files():
    """Make sure the model FILES are on disk — no RAM, and no network when they are already
    cached. Loading from the local folder keeps every later reload offline-safe."""
    global model_path
    try:
        from huggingface_hub import snapshot_download
        try:
            model_path = snapshot_download(MODEL, local_files_only=True)
        except Exception:
            print('[whisper] Model files missing — downloading (~1.5 GB first run)', flush=True)
            model_path = snapshot_download(MODEL)
        print(f'[whisper] Model files ready (not loaded until first use): {model_path}', flush=True)
    except Exception as e:
        print(f'[whisper] Could not resolve local model files ({e}) — loading by name on first use', flush=True)
    finally:
        model_ready.set()  # unblock transcriptions even on failure


@app.route('/warm', methods=['POST'])
def warm():
    """Backlog #226b: the renderer calls this when Zani PRESSES the mic (tap-to-talk or hands-free
    start), so the ~1 s load runs while he speaks instead of after. Fire-and-forget on the
    renderer side. It runs on the same _mlx worker as /transcribe, so a transcription that
    arrives during the load waits for it. It calls the SAME loader with the SAME arguments that transcribe() uses
    (ModelHolder.get_model(path, float16), which also mx.eval()s the weights) and decodes
    nothing, so even in the worst case (he speaks for less than the load time) the total is the
    same work as loading inside /transcribe — never more. (A first version decoded a silent clip
    to load; that added a decode to the worst case.)"""
    if not model_ready.wait(timeout=0.01):
        return jsonify({'status': 'files-not-ready', 'loaded': False})
    status = _mlx.submit(_warm_job).result()
    return jsonify({'status': status, 'loaded': status != 'error'}), (500 if status == 'error' else 200)


def _warm_job():
    global _last_use
    _last_use = time.time()
    if model_loaded():
        return 'already-loaded'
    t0 = time.time()
    try:
        import mlx.core as mx
        _model_holder().get_model(model_path, mx.float16)   # = transcribe()'s own load (fp16 default)
        print(f'[whisper] Model loaded by mic prewarm ({time.time() - t0:.2f}s)', flush=True)
        return 'loaded'
    except Exception as e:
        print(f'[whisper] prewarm failed: {e}', flush=True)
        return 'error'
    finally:
        _last_use = time.time()


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model_ready': model_ready.is_set(), 'model_loaded': model_loaded()})


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'no audio file'}), 400

    # Wait for model to be ready (up to 5 min covers first-run download)
    ready = model_ready.wait(timeout=300)
    if not ready:
        return jsonify({'error': 'model not ready — still loading'}), 503

    audio_file = request.files['audio']
    # Hands-free sends WAV (Silero VAD PCM); manual mode sends webm. Derive the
    # suffix from the upload name, whitelisted — ffmpeg keys container off it.
    ext = os.path.splitext(audio_file.filename or '')[1].lower()
    suffix = ext if ext in ('.webm', '.wav', '.ogg', '.mp3') else '.webm'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    def job():
        global _last_use
        was_loaded, t0 = model_loaded(), time.time()
        try:
            return mlx_whisper.transcribe(tmp_path, path_or_hf_repo=model_path, language='en'), was_loaded, t0
        finally:
            _last_use = time.time()

    try:
        result, was_loaded, t0 = _mlx.submit(job).result()
        if not was_loaded:
            print(f'[whisper] Model loaded on first use (load + transcribe {time.time() - t0:.2f}s)', flush=True)
        transcript = result['text'].strip()
        # No-speech gate signals (#46): Whisper already computes per-segment
        # no_speech_prob and avg_logprob during decoding — surface the worst of
        # each so the frontend can discard VAD false-positives (breath, noise)
        # instead of sending them as messages. No segments at all = certain
        # non-speech. Extra fields are ignored by the manual voice path.
        segs = result.get('segments') or []
        no_speech = max((s.get('no_speech_prob', 0.0) for s in segs), default=1.0)
        avg_lp    = min((s.get('avg_logprob', 0.0) for s in segs), default=-10.0)
        # Backlog #205: Whisper's third failure signal. A repetition loop is CONFIDENT,
        # so it passes the two above; its text compresses well. Whisper already
        # computed this per segment (and kept the last try when every temperature
        # fallback failed). Per SEGMENT, as Whisper uses it: on a whole long transcript
        # natural English drifts toward 2.4.
        compression = max((s.get('compression_ratio', 0.0) for s in segs), default=0.0)
        print(f'[whisper] Transcript: {transcript!r} no_speech={no_speech:.2f} logprob={avg_lp:.2f} '
              f'compression={compression:.2f} segments={len(segs)}')
        return jsonify({'transcript': transcript,
                        'no_speech_prob': round(no_speech, 3),
                        'avg_logprob': round(avg_lp, 3),
                        'compression_ratio': round(compression, 3)})
    except Exception as e:
        print(f'[whisper] Error: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


if __name__ == '__main__':
    print('[whisper] Starting on port 5004')
    threading.Thread(target=_ensure_files, daemon=True).start()
    threading.Thread(target=_idle_unloader, daemon=True).start()
    app.run(host='127.0.0.1', port=5004, debug=False, threaded=True)
