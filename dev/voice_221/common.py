"""Shared helpers for backlog #221 (her tsundere/flustered voice). See PREREG_221.md.

Every synthesis goes through the SHIPPED fish_tts() (imported, never copied), so the
payload is byte-identical to production except for the text. The wallet guard stops a
run before it spends more than the approved cap (plan fix 32).
"""
import hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
AMADEUS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, AMADEUS)
AUDIO = os.path.join(AMADEUS, 'dev', 'voice_test', '221')   # git-ignored (.gitignore:26)
os.makedirs(AUDIO, exist_ok=True)

import requests
import kurisu_fish_server as fs

CAP_USD = 0.40
WALLET_URL = 'https://api.fish.audio/wallet/self/api-credit'


def app_running():
    return subprocess.run(['pgrep', '-x', 'Amadeus'], capture_output=True).returncode == 0


def wallet():
    r = requests.get(WALLET_URL, headers={'Authorization': f'Bearer {fs.FISH_API_KEY}'}, timeout=15)
    r.raise_for_status()
    return float(r.json()['credit'])


USD_PER_BYTE = 15.0 / 1_000_000     # Fish API price: $15 per 1M UTF-8 bytes (s2-pro)
MARGIN = 1.5                        # the bill is not visible in real time, so over-estimate


class Guard:
    """Stops a run BEFORE a call that would take the estimated spend over the cap.

    The wallet is NOT a real-time signal: on 2026-09-30 it did not move after 4 clips
    (its updated_at was the previous evening), so a guard that reads it would never stop.
    The estimate counts the UTF-8 bytes of every text sent, x MARGIN. The wallet is read
    at start and end only, for the record."""
    def __init__(self, cap=CAP_USD, spent_before=0.0):
        self.start = wallet()
        self.cap, self.est = cap, spent_before   # spent_before: earlier runs under the same cap
        print(f'[guard] wallet ${self.start:.4f}, cap ${cap:.2f}, estimated already ${spent_before:.4f}')

    def charge(self, text):
        cost = len(text.encode('utf-8')) * USD_PER_BYTE * MARGIN
        if self.est + cost > self.cap:
            sys.exit(f'STOP: next clip would take the estimate to ${self.est + cost:.4f} > cap ${self.cap:.2f}')
        self.est += cost

    def report(self):
        w = wallet()
        print(f'[guard] estimated spend ${self.est:.4f}; wallet ${self.start:.4f} -> ${w:.4f} '
              f'(the wallet may lag)')
        return {'estimated_usd': round(self.est, 4), 'wallet_start': self.start, 'wallet_end': w}


def synth(text, path, guard=None, payload_override=None, model=None):
    """One clip through the shipped fish_tts (or an explicit payload for the Step 0 control).
    `model` (payload_override only) replaces the model header — #221b's s2.1-pro-free arms.
    No retry on 4xx (402 = out of credit: stop). One retry on 5xx or a timeout."""
    for attempt in range(2):
        if guard:
            guard.charge(text)          # a retry is billed too, so it is charged too
        try:
            if payload_override is None:
                audio = fs.fish_tts(text)
            else:
                r = requests.post(fs.FISH_API_URL, json=payload_override, timeout=60,
                                  headers={'Authorization': f'Bearer {fs.FISH_API_KEY}',
                                           'Content-Type': 'application/json', 'model': model or fs.FISH_MODEL})
                r.raise_for_status()
                audio = r.content
            break
        except requests.HTTPError as e:
            code = e.response.status_code
            if code < 500 or attempt == 1:
                sys.exit(f'STOP: Fish HTTP {code}: {e.response.text[:200]}')
        except requests.Timeout:
            if attempt == 1:
                sys.exit('STOP: Fish timed out twice')
    with open(path, 'wb') as f:
        f.write(audio)
    return hashlib.sha256(audio).hexdigest()


def duration(path):
    return float(subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())


def internal_pauses(path, noise='-35dB', d=0.15, edge=0.05):
    """silencedetect pauses, WITHOUT the silence touching the start or end (plan fix 14)."""
    dur = duration(path)
    err = subprocess.run(['ffmpeg', '-i', path, '-af', f'silencedetect=noise={noise}:d={d}',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', err)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else dur          # a silence still open at EOF
        if s <= edge or e >= dur - edge:
            continue
        out.append(round(e - s, 3))
    return dur, out


def loudness(path):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', err)
    return float(m[-1]) if m else None
