#!/usr/bin/env python3
"""
kurisu_fish_server.py — Fish Audio S2 Pro TTS Server for Amadeus
Replaces kurisu_elevenlabs_server.py
Run: python3 kurisu_fish_server.py
"""

import base64
import json
import os
import random
import re
import sys
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── CREDENTIALS — loaded from config.json (git-ignored, never in source) ──
# config.json shape: {"fish_api_key": "...", "deepl_api_key": "..."}
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    with open(_CONFIG_PATH) as _f:
        _config = json.load(_f)
    FISH_API_KEY  = _config['fish_api_key']
    DEEPL_API_KEY = _config['deepl_api_key']
except Exception as _e:
    sys.exit(f'[TTS] FATAL: cannot read credentials from {_CONFIG_PATH}: {_e}')

# ── FISH AUDIO CONFIG ──────────────────────────────────────────
FISH_VOICE_ID  = "c4d832799bf845ee86638a1bc0cd0d41"  # Neutral baseline — rich tags drive emotion
FISH_API_URL   = "https://api.fish.audio/v1/tts"
FISH_MODEL     = "s2-pro"

# ── DEEPL TRANSLATION CONFIG (primary — reliable) ──────────────
DEEPL_URL      = "https://api-free.deepl.com/v2/translate"

# ── EMOTION → S2 TAG MAPPING ──────────────────────────────────
# Fish Audio S2 supports free-form emotion tags in text
EMOTION_TAGS = {
    # ── Each tag is written as a voice actor direction ──
    # S2 Pro treats these as natural language instructions, not fixed labels.
    # Descriptions include pitch, pace, texture, and physical quality of voice.

    "happy":        "[warm and genuinely bright, speaking at a natural upbeat pace, voice carrying a real smile, slightly higher pitch than usual, light and clear]",
    "excited":      "[rushing forward with energy, pitch climbing, words tumbling out faster than intended, barely containing enthusiasm, voice bright and sharp]",
    "sad":          "[quiet and heavy, speaking slowly with long pauses, voice slightly rough at the edges, trailing off at the end of phrases, restrained grief]",
    "angry":        "[clipped and sharp, biting off each word, low controlled fury rather than shouting, jaw tight, speaking through clenched teeth, pitch dropping dangerously]",
    "scared":       "[small and quiet, voice trembling slightly on certain syllables, speaking carefully as if afraid to make noise, breath audible, hesitant]",
    "surprised":    "[sharp intake of breath before speaking, pitch jumping up suddenly, voice bright and unguarded, words coming out fast and unfiltered]",
    "smug":         "[slow and deliberate, savoring each word, voice dropping lower with confidence, dry amusement barely concealed, intellectual superiority dripping from every syllable]",
    "embarrassed":  "[quieter higher voice, slight stammer on first syllable, quickening then self-caught delivery, tsundere warmth under defensiveness, cheeks-flushed quality]",
    "calm":         "[calm, measured, unhurried, clear]",
    "thinking":     "[slow deliberate pace, long mid-sentence pauses, slightly lower voice, internal-monologue quality, trailing-off-then-returning rhythm]",
    "default":      "[composed and clear, natural conversational pace for a confident young woman, neither warm nor cold, simply present]",
    "tsundere":     "[starts sharp and defensive with slightly raised pitch, voice catching in the middle as warmth leaks through despite herself, ends clipped to cover it up, flustered undercurrent throughout]",
    "sarcastic":    "[completely flat and deadpan, each word landing with surgical precision, zero emotional variation, dry amusement so controlled it barely registers, slight pause before punchline]",
    "flustered":    "[pitch rising too fast, words stumbling and overlapping, speaking too quickly then halting, voice going quiet at the end in embarrassment, completely losing composure]",
    "dismissive":   "[slow exhale before speaking, bored and unimpressed, voice barely rising, each word measured out like she begrudges the effort, faint disbelief at having to respond at all]",
    "curious":      "[intent forward quality, precise analytical edge, quickening investigative pace, slightly elevated pitch, heightened vocal projection, questioning upward lift]",
    "lecture":      "[authoritative and precise, voice carrying academic confidence, measured cadence, each point landed cleanly, slight sharpness when correcting, professor giving a correction]",
    "melancholic":  "[soft and wistful, slow delivery with quiet weight, voice with something unspoken, gentle sadness in the pauses, reflective and distant]",
    "teasing":      "[light and playful, barely suppressing laughter, voice lilting upward, words drawn out slightly for effect, warmth that she would deny if called out]",
    "annoyed":      "[sharp sigh before speaking, tired and exasperated, clipped pace, voice flattening with impatience, emphasis on specific words like she has explained this too many times]",
    # Legacy aliases
    "smile":        "[warm and genuinely bright, speaking at a natural upbeat pace, voice carrying a real smile, slightly higher pitch than usual, light and clear]",
    "blush":        "[quieter higher voice, slight stammer on first syllable, quickening then self-caught delivery, tsundere warmth under defensiveness, cheeks-flushed quality]",
    "very_blush":   "[pitch rising too fast, words stumbling and overlapping, speaking too quickly then halting, voice going quiet at the end in embarrassment, completely losing composure]",
    "serious":      "[authoritative and precise, voice carrying academic confidence, measured cadence, each point landed cleanly, slight sharpness when correcting, professor giving a correction]",
    "wink":         "[light and playful, barely suppressing laughter, voice lilting upward, words drawn out slightly for effect, warmth that she would deny if called out]",
}

# ── Emotion-dependent speech speed ──
# Kurisu baseline: 1.2 (confident researcher, slightly faster than neutral)
# Adjusted per emotion to match canonical Steins;Gate voice acting pacing
EMOTION_SPEED = {
    "happy":        1.2,
    "excited":      1.35,   # rushing, barely containing energy
    "sad":          0.9,    # heavy and slow
    "angry":        1.25,   # clipped and fast
    "scared":       0.95,   # careful, afraid to make noise
    "surprised":    1.3,    # words coming out fast and unfiltered
    "smug":         1.05,   # deliberate, savoring every word
    "embarrassed":  1.2,    # speeds up then catches herself
    "calm":         1.1,    # measured, unhurried
    "thinking":     1.0,    # slow and deliberate
    "default":      1.2,    # Kurisu baseline
    "tsundere":     1.2,    # sharp start, softening through
    "sarcastic":    1.05,   # flat and deliberate
    "flustered":    1.35,   # stumbling fast then halting
    "dismissive":   1.05,   # barely rising, begrudges the effort
    "curious":      1.2,    # pace picks up as interest catches
    "lecture":      1.1,    # measured academic cadence
    "melancholic":  0.9,    # slow with quiet weight
    "teasing":      1.2,    # lilting and playful
    "annoyed":      1.2,    # clipped with impatience
    # Legacy aliases
    "smile":        1.2,
    "blush":        1.2,
    "very_blush":   1.35,
    "serious":      1.1,
    "wink":         1.2,
}

# Tracks last used emotion for consecutive-same-emotion variation
_last_emotion = {"value": None, "count": 0}


def compute_speed(emotion: str, japanese_text: str) -> float:
    """
    Computes a naturalistically varied speech speed for Kurisu.

    Combines multiple conditions that drive rate variation in real speech:
      1. Emotion base speed (from EMOTION_SPEED)
      2. Text length modifier — short text feels clipped, long text she rushes
      3. Sentence-ending punctuation — questions slow slightly, exclamations push
      4. Multi-sentence responses — she speeds up slightly across longer replies
      5. Micro-randomisation — same emotion never sounds identical twice
      6. Consecutive same emotion — extra nudge to prevent locked-in monotony

    All values clamped to Fish Audio API range: 0.5–2.0
    """
    base = EMOTION_SPEED.get(emotion, 1.2)
    modifier = 0.0

    # ── 1. Text length modifier ──
    # Short Japanese text (<12 chars): feels more clipped → slightly faster
    # Very long Japanese text (>80 chars): she rushes through thoughts → faster
    text_len = len(japanese_text)
    if text_len < 12:
        modifier += 0.05
    elif text_len > 80:
        modifier += 0.04
    elif text_len > 50:
        modifier += 0.02

    # ── 2. Sentence-ending punctuation modifier ──
    stripped = japanese_text.rstrip()
    if stripped.endswith('？') or stripped.endswith('?'):
        modifier -= 0.05   # questions trail off slightly
    elif stripped.endswith('！') or stripped.endswith('!'):
        modifier += 0.04   # exclamations carry energy forward

    # ── 3. Multi-sentence modifier ──
    # Count full stops — multiple sentences = she's in flow, speed picks up
    sentence_count = japanese_text.count('。') + japanese_text.count('.')
    if sentence_count >= 3:
        modifier += 0.04
    elif sentence_count == 2:
        modifier += 0.02

    # ── 4. Micro-randomisation ──
    # Gaussian noise centred on 0, std ≈ 0.03 — never more than ±0.05
    # Ensures the same emotion never sounds identical twice
    noise = random.gauss(0, 0.03)
    noise = max(-0.05, min(0.05, noise))
    modifier += noise

    # ── 5. Consecutive same emotion nudge ──
    global _last_emotion
    if _last_emotion["value"] == emotion:
        _last_emotion["count"] += 1
        if _last_emotion["count"] >= 2:
            # Nudge away from the locked-in pace after 2+ same emotions in a row
            nudge = random.choice([-0.04, -0.03, 0.03, 0.04])
            modifier += nudge
    else:
        _last_emotion["value"] = emotion
        _last_emotion["count"] = 1

    final = base + modifier
    # Clamp to Fish Audio API range
    final = round(max(0.5, min(2.0, final)), 3)
    return final


# Names/terms that DeepL mangles — replace after translation
JP_FIXES = {
    "まきせ くりす": "牧瀬クリス",
    "マキセ・クリス": "牧瀬クリス",
    "マキセ・ブニス": "牧瀬クリス",
    "マキセ クリス": "牧瀬クリス",
    "紅莉栖": "クリス",      # Replace rare kanji with katakana for correct pronunciation
    "オカリン": "岡部倫太郎",
    "ダル": "橋田至",
    "シュタインズ・ゲート": "Steins;Gate",
}

def fix_japanese(text: str) -> str:
    """Fix known mistranslations and name mangling."""
    for wrong, right in JP_FIXES.items():
        text = text.replace(wrong, right)
    return text


def add_prosody_tags(japanese_text: str, emotion: str) -> str:
    """
    Injects Fish Audio S2 Pro prosody tags into Japanese text.
    Tags only go to Fish Audio — never returned to the frontend.

    Pause duration basis (speech naturalness research):
      comma  (、) ≈ 300ms → [short pause]
      period (。) ≈ 600ms → [pause]
      ellipsis (…) ≈ 900ms → [pause, hesitating quietly]
      exclamation (！)     → [exhale]
      question (？)        → [short pause]
      dash (—)             → [short pause]
    """
    import re

    # ── 1. No separate opener (bug 14) ──
    # Opener sounds live only inside the EMOTION_TAGS style instructions —
    # separate English opener tags were vocalised as speech by Fish Audio.
    # The dead EMOTION_OPENER dict was removed July 13, 2026 (#30, git history).
    text = japanese_text

    # ── 2. Emotion arousal groupings for breath-sound decisions ──
    # Research (Journal of Speech, Language and Hearing Research, 2023):
    # In healthy speakers at rest, breathing is inaudible. Audible breathing
    # only occurs in speech under high physiological or emotional arousal.
    # Calm/neutral speech → silent pauses, no exhale tags.
    # High-arousal speech → exhale/breath tags are natural and expected.

    HIGH_AROUSAL  = {"angry", "annoyed", "excited", "scared",
                     "surprised", "flustered", "embarrassed"}
    MED_AROUSAL   = {"happy", "teasing", "smug"}
    # Everything else: calm, default, thinking, lecture, curious,
    # dismissive, sarcastic, tsundere, melancholic, sad → low arousal

    # ── 3. Inline punctuation pause tags ──
    # Injected AFTER punctuation. Pause style and breath sound depend on emotion.

    # Ellipsis — trailing off, hesitating (always — this is about thought, not breath)
    text = text.replace("…", "… [pause, hesitating quietly]")
    text = text.replace("...", "... [pause, hesitating quietly]")  # ascii fallback

    # Em dash — interrupted or cut-off thought
    text = text.replace("—", "— [short pause]")

    # Exclamation — breath only for high-arousal emotions
    # Research: exhale after exclamation is natural for emotional release,
    # but alien in calm/academic speech where exclamations indicate emphasis only.
    if emotion in HIGH_AROUSAL:
        text = text.replace("！", "！[exhale]")
        text = text.replace("!", "![exhale]")
    elif emotion in MED_AROUSAL:
        text = text.replace("！", "！[soft exhale]")
        text = text.replace("!", "![soft exhale]")
    else:
        # Low arousal — exclamation is just emphasis, no breath sound
        text = text.replace("！", "！[pause]")
        text = text.replace("!", "![pause]")

    # Question mark — brief pause, rising intonation held (same across emotions)
    text = text.replace("？", "？[short pause]")
    text = text.replace("?", "?[short pause]")

    # Full stop (。) — pause style depends on arousal level
    # High arousal: [pause] — Fish Audio may naturally add breath here (appropriate)
    # Low arousal:  [silent pause] — explicit no-breath instruction
    if emotion in HIGH_AROUSAL or emotion in MED_AROUSAL:
        text = text.replace("。", "。[pause]")
    else:
        text = text.replace("。", "。[silent pause]")

    # Comma (、) — brief clause beat
    # High arousal: [short pause] — natural breath between clauses
    # Low arousal:  [brief pause, no breath] — clean rhythmic beat only
    if emotion in HIGH_AROUSAL:
        text = text.replace("、", "、[short pause]")
        text = text.replace("，", "，[short pause]")
    else:
        text = text.replace("、", "、[brief pause, no breath]")
        text = text.replace("，", "，[brief pause, no breath]")

    # ── 3. Emotion-specific mid-speech enhancements ──
    # Add a [sigh] mid-line for long annoyed/dismissive responses.
    # Heuristic: if text is long (>40 chars) and emotion fits, inject after first 。[pause]
    SIGH_EMOTIONS = {"annoyed", "dismissive", "sad", "melancholic"}
    if emotion in SIGH_EMOTIONS and len(text) > 40:
        # Insert [sigh] after the first sentence pause to break up long lines naturally
        p_tag = "。[pause]" if (emotion in HIGH_AROUSAL or emotion in MED_AROUSAL) else "。[silent pause]"
        text = text.replace(p_tag, p_tag + " [sigh]", 1)

    # ── 3b. Mid-sentence emotion re-anchoring ──
    # After each sentence pause (except the last), inject a brief re-anchor tag.
    # Without this, Fish Audio drifts back to neutral between sentences.
    # Research: emotional prosody is suprasegmental — it must be re-established
    # across sentence boundaries, not just set once at the opener.
    EMOTION_ANCHOR = {
        "happy":        "[still warm and bright]",
        "excited":      "[still energised]",
        "sad":          "[still subdued]",
        "angry":        "[still tense and controlled]",
        "scared":       "[still careful and quiet]",
        "surprised":    "[still caught off guard]",
        "smug":         "[still savoring every word]",
        "embarrassed":  "[still flustered]",
        "calm":         "[still measured]",
        "thinking":     "[still deliberate]",
        "tsundere":     "[still guarded, warmth leaking through]",
        "sarcastic":    "[still deadpan]",
        "flustered":    "[still losing composure]",
        "dismissive":   "[still unimpressed]",
        "curious":      "[still analytical edge]",
        "lecture":      "[continuing with authority]",
        "melancholic":  "[still wistful and quiet]",
        "teasing":      "[still holding back a laugh]",
        "annoyed":      "[still exasperated]",
    }
    anchor = EMOTION_ANCHOR.get(emotion, "")
    if anchor and "。[pause]" in text:
        # Inject anchor after every 。[pause] EXCEPT the last one
        # (last sentence needs no re-anchor — response is ending)
        # Split on either pause style — handles both [pause] and [silent pause]
        pause_tag = "。[pause]" if (emotion in HIGH_AROUSAL or emotion in MED_AROUSAL) else "。[silent pause]"
        parts = text.split(pause_tag)
        if len(parts) >= 2:
            # 2+ sentence boundaries — re-anchor all but the final gap
            # len(parts) >= 2 catches the common 2-sentence response case
            text = (pause_tag + " " + anchor + " ").join(parts[:-1]) + pause_tag + parts[-1]

    # Emphasis on key words for lecture/smug — make her sound more authoritative
    # Fish Audio applies [emphasis] to whatever word follows it
    EMPHASIS_EMOTIONS = {"lecture", "smug", "angry"}
    if emotion in EMPHASIS_EMOTIONS:
        # Add emphasis before the first word after the opener
        text = "[emphasis] " + text

    # ── 4. Final assembly ──
    result = text

    # ── 5. Clean up double spaces ──
    result = re.sub(r"  +", " ", result)
    result = result.strip()

    return result

# ── TRANSLATOR CORE ──────────────────────────────────────────────────────────
# July 18 2026 A/B (dev/translate_ab_test.py, results in translate_ab_results.json):
# gemma4 register-aware translation beat DeepL 7/8 on quality and 8/8 on REGISTER
# — feminine sentence-final particles (わよ/のよ/のね), 私 first person, preserved
# stammers — things a generic MT engine cannot do (DeepL even produced written-
# paper register ものである for spoken lines). Latency ~1s warm.
# The July note here claimed a "+0.57s KV-cache penalty on the following chat
# turn". RE-MEASURED 2026-09-07 on Ollama 0.33.3 (backlog #196): that penalty is
# +2ms. The July figure was WALL time of a 3-token request, which mixes prefill,
# decode and scheduling; measured as prompt_eval_duration the chat prefix survives
# an interleaved translate call (148ms for 5,322 tokens over 10 alternating turns).
# Translate costs ~1019ms and nothing extra on the following turn.
# Re-confirmed 2026-09-07 on 30 real replies: DeepL is 392ms vs gemma4's 1022ms but
# loses register on every axis (feminine endings 56.7%->23.3%, polite desu/masu
# 0%->6.7%, calls him 君 0%->20%) and invented a fact. gemma4 stays.
# Set TRANSLATOR='deepl' to revert instantly. gemma failure falls back to DeepL,
# DeepL failure returns None (frontend does the silent text-only reveal).
TRANSLATOR = 'gemma4'
OLLAMA_CHAT_URL = 'http://127.0.0.1:11434/api/chat'
KURISU_REGISTER_PROMPT = (
    "You are a professional Japanese dialogue translator for Makise Kurisu "
    "(Steins;Gate): an 18-year-old female genius scientist, tsundere, speaking "
    "CASUALLY to a close friend. Translate the English line into natural spoken "
    "Japanese in HER register: casual feminine speech (わ/のよ/じゃない endings "
    "where natural, never masculine だぜ/だろ), first person 私, clipped and "
    "direct, keep stammers (W-what → な、何) and '...' pauses. Preserve the name "
    "Zani as ザンニー and Kurisu as クリス. Output ONLY the Japanese translation "
    "— no romaji, no explanations, no quotes."
)

def translate_via_gemma(text):
    """Register-aware EN→JA via local gemma4. Returns None on failure.
    num_ctx MUST be 8192 — any other value forces a full model reload (bug 33 family)."""
    for attempt in range(2):
        try:
            r = requests.post(OLLAMA_CHAT_URL, json={
                'model': 'gemma4:latest',
                'messages': [{'role': 'system', 'content': KURISU_REGISTER_PROMPT},
                             {'role': 'user', 'content': text}],
                'stream': False, 'think': False, 'keep_alive': '30m',
                'options': {'temperature': 0.3, 'num_predict': 150, 'num_ctx': 8192},
            }, timeout=20)
            r.raise_for_status()
            out = r.json()['message']['content'].strip()
            # Defensive cleanup: stray quotes/labels, collapse multi-line to one line
            out = out.strip('「」"\' ')
            out = ' '.join(line.strip() for line in out.splitlines() if line.strip())
            if out.lower().startswith('japanese:'):
                out = out[9:].strip()
            if out:
                return fix_japanese(out)
        except Exception as e:
            print(f"[TTS] gemma translate failed (attempt {attempt + 1}/2): {e}")
    return None


# P1: which engine actually produced the last translation.  gemma4 runs on the
# SAME GPU that renders her (CLAUDE.md 37), DeepL is network — so the trace has
# to say which one paid for the time, not just how long it took.
_last_translator = None


def translate_to_japanese(text):
    """Translator front door: register-aware gemma4 first, DeepL as fallback."""
    global _last_translator
    if TRANSLATOR == 'gemma4':
        jp = translate_via_gemma(text)
        if jp:
            _last_translator = 'gemma4'
            return jp
        print("[TTS] gemma unavailable — falling back to DeepL")
    _last_translator = 'deepl'
    return translate_via_deepl(text)


def translate_via_deepl(text):
    """Translate English to Japanese using DeepL API (fallback since July 2026)."""
    # Pre-process: protect proper nouns from DeepL mangling
    protected = text
    protected = protected.replace("Makise Kurisu", "牧瀬クリス")
    protected = protected.replace("Kurisu Makise", "牧瀬クリス")
    protected = protected.replace("Kurisu", "クリス")
    protected = protected.replace("Zani", "ザンニー")   # user's name — pronounced zan-nii
    protected = protected.replace("Okabe", "岡部")
    protected = protected.replace("Rintaro", "倫太郎")
    protected = protected.replace("Amadeus", "アマデウス")

    headers = {
        'Authorization': f'DeepL-Auth-Key {DEEPL_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'text': [protected],
        'target_lang': 'JA'
    }
    for attempt in range(2):
        try:
            response = requests.post(
                'https://api-free.deepl.com/v2/translate',
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            return fix_japanese(result['translations'][0]['text'])
        except Exception as e:
            print(f"[TTS] DeepL translation failed (attempt {attempt + 1}/2): {e}")
    # Both attempts failed. Return None so /speak degrades to a silent text-only
    # reveal in the frontend (the data.audio_b64=null path it already handles).
    # The old behaviour — sending the ENGLISH text to Fish Audio — made Kurisu
    # speak English through the Japanese voice model, which is worse than silence.
    return None


def fish_tts(tagged_text: str, speed: float = 1.2) -> bytes:
    """Call Fish Audio S2 Pro API and return raw MP3 bytes. Text should already be emotion-tagged."""
    payload = {
        "text": tagged_text,
        "reference_id": FISH_VOICE_ID,
        "format": "mp3",
        "mp3_bitrate": 128,
        "latency": "normal",
        "normalize": True,        # V3 config: tighter, more consistent prosody won the A/B listen test
        "chunk_length": 200,
        "temperature": 0.7,        # V3 config: less prosody randomness — stability over variation
        "top_p": 0.8,               # Fish Audio recommended: broader sampling diversity
        "repetition_penalty": 1.2,  # Prevents Fish Audio phoneme loop bug
        "speed": round(max(0.5, min(2.0, speed)), 2),  # Fish Audio cloud: 0.5–2.0
    }

    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
        "model": FISH_MODEL,
    }

    response = requests.post(
        FISH_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    print(f"[TTS] Fish Audio response: status={response.status_code}")
    response.raise_for_status()
    return response.content


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "").strip()
    emotion = data.get("emotion", "default").lower()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    print(f"[TTS] Received: {text[:50]}... emotion={emotion}")

    try:
        # Step 1: Translate to Japanese
        # P1 (backlog #186): time the two server-side stages.  These go back to
        # the renderer as DURATIONS in milliseconds, never as timestamps — this
        # process's clock cannot be compared with the renderer's performance.now().
        _t_translate_start = time.perf_counter()
        japanese_text = translate_to_japanese(text)
        translate_ms = int((time.perf_counter() - _t_translate_start) * 1000)
        if japanese_text is None:
            # Translation unavailable — tell the frontend "no audio" so it falls
            # back to the estimated word reveal (same shape as the null-audio path).
            print("[TTS] Translation unavailable — returning no-audio response")
            return jsonify({"audio_b64": None, "char_timings": None, "japanese": None,
                            "error": "translation unavailable",
                            "timings": {"translate_ms": translate_ms, "fish_ms": None,
                                        "translator": _last_translator}})
        print(f"[TTS] Translated: {japanese_text[:50]}...")

        # Step 2: NO inline prosody tags — "V3" config from the July 2026 voice A/B
        # test (dev/voice_ab_test.py). Dense per-punctuation tags measured a 1.19s
        # dead-air outlier mid-utterance (natural band is 0.2-0.6s within sentences);
        # untagged Japanese let Fish's native punctuation prosody land every pause
        # in 0.17-0.58s. Zani picked V3 by ear. Emotion pacing/breath still comes
        # from the EMOTION_TAGS style instruction prepended in Step 3.
        # (add_prosody_tags kept below for reference / possible partial reintroduction.)

        # Step 3: Prepend global emotion tag for voice direction
        tag = EMOTION_TAGS.get(emotion, "")
        tagged_text = f"{tag} {japanese_text}".strip() if tag else japanese_text
        print(f"[TTS] Full tagged text → Fish Audio:\n  {tagged_text}")

        # Step 4: Generate audio via Fish Audio S2 Pro
        # Fixed 1.1 speed (V3 config): compute_speed's turn-to-turn variance
        # (measured 1.087 → 1.22 on consecutive turns, a 12% pace lurch) was the
        # "speed sounds weird" complaint. Emotion pace nuance still comes from the
        # EMOTION_TAGS descriptions ("speaking slowly", "words tumbling out fast").
        speed = 1.1
        _t_fish_start = time.perf_counter()
        audio_bytes = fish_tts(tagged_text, speed=speed)
        fish_ms = int((time.perf_counter() - _t_fish_start) * 1000)
        print(f"[TTS] Speed: {speed}x (emotion={emotion}, jp_len={len(japanese_text)})")
        print(f"[TTS] P1 stages: translate={translate_ms}ms ({_last_translator}) fish={fish_ms}ms")
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        print(f"[TTS] Returning audio_b64 length: {len(audio_b64)}")

        # Return in format Amadeus expects
        # char_timings=null → wall clock timer handles English word reveal
        return jsonify({
            "elevenlabs": True,      # reuse existing sync logic in amadeus.html
            "audio_b64": audio_b64,
            "char_timings": None,    # wall clock timer handles English
            "total_duration": 0,     # not needed — wall clock is independent
            "japanese": japanese_text,
            # P1 — durations only, in ms.  The renderer treats a missing or
            # malformed block as "unknown" and records nothing for these fields.
            "timings": {"translate_ms": translate_ms, "fish_ms": fish_ms,
                        "translator": _last_translator},
        })

    except requests.HTTPError as e:
        print(f"[TTS] Fish Audio API error: {e.response.status_code} — {e.response.text}")
        return jsonify({"error": f"Fish Audio API error: {e.response.status_code}"}), 500
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "tts": "fish-audio-s2-pro"})


if __name__ == "__main__":
    print("="*50)
    print("  Kurisu Fish Audio S2 Pro TTS Server")
    print(f"  Voice: 牧瀬クリス ({FISH_VOICE_ID[:8]}...)")
    print("  Model: s2-pro")
    print("  Port:  5002")
    print("="*50)
    app.run(host="127.0.0.1", port=5002, debug=False)
