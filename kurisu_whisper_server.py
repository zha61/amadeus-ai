import os
# Ensure Homebrew binaries (ffmpeg etc.) are findable — Electron doesn't inherit
# the full shell PATH, same issue as PYTHON/OLLAMA hardcoded paths (bugs 10, 19, 27).
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

from flask import Flask, request, jsonify
import mlx_whisper
import tempfile
import threading
import wave
import struct

app = Flask(__name__)

# large-v3-turbo (809M): accuracy within ~0.4pt WER of full large-v3 — clearly
# better than the previous whisper-medium — at ~4x realtime on Apple Silicon,
# in the same ~1.5GB memory class. 2026 consensus pick for local Mac STT.
# Swapped July 18, 2026 after download + functional verification; medium deleted.
MODEL = 'mlx-community/whisper-large-v3-turbo'
model_ready = threading.Event()


def _warmup():
    """Load and cache the model at startup so first real transcription is fast."""
    print(f'[whisper] Loading model: {MODEL}')
    print('[whisper] Downloading if needed (~1.5 GB first run) — server is ready for health checks')
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        warmup_path = f.name
    # Write a 0.1s silent WAV using stdlib only (no soundfile/numpy needed)
    with wave.open(warmup_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        num_frames = 1600
        wf.writeframes(struct.pack('<' + 'h' * num_frames, *([0] * num_frames)))
    try:
        mlx_whisper.transcribe(warmup_path, path_or_hf_repo=MODEL, language='en')
        print('[whisper] Model ready')
        model_ready.set()
    except Exception as e:
        print(f'[whisper] Warmup failed: {e}')
        model_ready.set()  # unblock transcriptions even on failure
    finally:
        try:
            os.unlink(warmup_path)
        except Exception:
            pass


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model_ready': model_ready.is_set()})


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

    try:
        result = mlx_whisper.transcribe(tmp_path, path_or_hf_repo=MODEL, language='en')
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
    threading.Thread(target=_warmup, daemon=True).start()
    app.run(host='127.0.0.1', port=5004, debug=False, threaded=True)
