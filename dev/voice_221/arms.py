"""#221 arms — the ONE place the arm texts live (PREREG_221.md). A ship test compares the
shipped /speak output with tagged_text() of the chosen arm, so nothing may be copied.

A  = shipped EMOTION_TAGS, byte-exact, nothing else (read from kurisu_fish_server at import).
B  = short tags: every comma-fragment ends in an acoustic noun (CLAUDE.md 32 / bugs.md 22a),
     no gerund-start clause (CLAUDE.md 15 / bugs.md 22), one quality, no arc; words from
     Fish's own docs ([embarrassed], [nervous]).
C  = B + a short re-anchor at the START of every sentence after the first (H1: Fish applies
     a tag "until the next tag or end of the sentence").
D  = A's tag + C's re-anchors. Run only if B loses and C wins (PREREG decision tree).
Only tsundere and flustered are touched; any other emotion returns arm A.
"""
import re
from common import fs     # common puts the repo root on sys.path

B_TAGS = {
    'tsundere':  '[embarrassed defensive voice, sharp edge, raised pitch, quick clipped pace]',
    'flustered': '[embarrassed nervous voice, high unsteady pitch, fast stumbling pace, quiet fading delivery]',
}
ANCHORS = {
    'tsundere':  '[embarrassed defensive voice]',
    'flustered': '[embarrassed nervous voice]',
}
# A sentence ends at a run of 。？！?! . "…" never ends one (e.g. "ただ…考えてただけ").
_SENT_END = re.compile(r'([。？！?!]+)')


def reanchor(jp, anchor):
    """Insert `anchor` at the start of every sentence after the first. Never after the last."""
    parts = _SENT_END.split(jp)          # [text, end, text, end, ..., tail]
    out, first = [], True
    for i in range(0, len(parts), 2):
        seg = parts[i]
        end = parts[i + 1] if i + 1 < len(parts) else ''
        if not seg.strip():
            out.append(seg + end)
            continue
        out.append((seg if first else f'{anchor} {seg.lstrip()}') + end)
        first = False
    return ''.join(out)


def sentences(jp):
    return [s for s in _SENT_END.split(jp)[0::2] if s.strip()]


def tagged_text(arm, emotion, jp):
    a_tag = fs.EMOTION_TAGS.get(emotion, '')
    if emotion not in B_TAGS or arm in ('A', "A'"):
        return f'{a_tag} {jp}'.strip() if a_tag else jp
    if arm == 'B':
        return f'{B_TAGS[emotion]} {jp}'
    if arm == 'C':
        return f'{B_TAGS[emotion]} {reanchor(jp, ANCHORS[emotion])}'
    if arm == 'D':
        return f'{a_tag} {reanchor(jp, ANCHORS[emotion])}'
    raise ValueError(arm)


if __name__ == '__main__':      # quick self-check of the split rules
    t = 'な、何？そういうこと言わないでよ。私、ただ…他のことに集中したいだけなの。コーディング、どう？'
    r = reanchor(t, '[X]')
    assert r == 'な、何？[X] そういうこと言わないでよ。[X] 私、ただ…他のことに集中したいだけなの。[X] コーディング、どう？', r
    assert reanchor('寝た方がいいよ…。別に。', '[X]') == '寝た方がいいよ…。[X] 別に。'
    assert reanchor('ひとつだけ。', '[X]') == 'ひとつだけ。'
    assert reanchor('ただ…考えてただけ', '[X]') == 'ただ…考えてただけ'
    assert reanchor('えっ?!本当?', '[X]') == 'えっ?![X] 本当?'
    assert len(sentences(t)) == 4 and len(sentences('ただ…考えてただけ。')) == 1
    for e in B_TAGS:
        assert tagged_text('A', e, 'あ。い。') == f'{fs.EMOTION_TAGS[e]} あ。い。'
    assert tagged_text('C', 'happy', 'あ。い。') == tagged_text('A', 'happy', 'あ。い。')
    print('arms self-check OK')
