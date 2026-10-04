"""#221b2 measurement helpers.

median_f0 is copied VERBATIM from voice_221b/screens_b.py (that file runs Whisper on import, so it
cannot be imported). It is a rough relative measure between arms, never an absolute pitch.
"""
import subprocess
import numpy as np


def median_f0(path, sr=16000, n=640, hop=160):
    """Rough autocorrelation pitch (Hz), voiced loud frames only. Used as a RELATIVE measure between arms."""
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    lo, hi, out = sr // 600, sr // 120, []
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n] * np.hanning(n)
        if np.sqrt((fr ** 2).mean()) < 0.02:
            continue
        ac = np.correlate(fr, fr, 'full')[n - 1:]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.4 * ac[0]:
            out.append(sr / k)
    return float(np.median(out)) if out else None
