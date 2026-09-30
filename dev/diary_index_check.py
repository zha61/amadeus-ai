#!/usr/bin/env python3
"""
dev/diary_index_check.py — is every diary entry in ChromaDB?  (backlog #218, bugs.md 95)

localStorage (`amadeus_diary_v1`, 50 entries max) is the SOURCE OF TRUTH.  The ChromaDB
collection `amadeus_diary` is a DERIVED index and a deliberate SUPERSET (it keeps entries that
aged out).  The boot index reconciles it.  This tool checks the invariant:

    every localStorage diary entry's text is a document in `amadeus_diary`

Read-only.  Works on COPIES in a temp folder (deleted afterwards).  Refuses to run while the
app is open.  Pure Python: LevelDB .log AND .ldb tables (Snappy) are decoded here, and the
record with the HIGHEST sequence number wins.  If the diary cannot be found or decoded it
EXITS 1 — it never reports "0 missing" for data it did not read (CLAUDE.md 52).

Usage:  python3 dev/diary_index_check.py [--chroma-copy PATH]   (PATH: use this sqlite as-is)
Exit:   0 = none missing · 3 = entries missing · 1 = could not check
"""
import glob, json, os, shutil, sqlite3, struct, subprocess, sys, tempfile

LS_DIR = os.path.expanduser('~/Library/Application Support/Amadeus/Local Storage/leveldb')
CHROMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'chroma', 'chroma.sqlite3')
KEY_SUFFIX = b'\x00\x01amadeus_diary_v1'   # Chromium key: _<origin>\x00\x01<key>


def die(msg):
    print('CANNOT CHECK: ' + msg)
    sys.exit(1)


def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if c < 0x80:
            return r, i


def snappy_decompress(b):
    n, i = varint(b, 0)
    out = bytearray()
    while i < len(b):
        tag = b[i]; i += 1; t = tag & 3
        if t == 0:
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59; ln = int.from_bytes(b[i:i + nb], 'little'); i += nb
            ln += 1; out += b[i:i + ln]; i += ln
            continue
        if t == 1:
            ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | b[i]; i += 1
        elif t == 2:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[i:i + 2], 'little'); i += 2
        else:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[i:i + 4], 'little'); i += 4
        for _ in range(ln):
            out.append(out[-off])
    if len(out) != n:
        raise ValueError('snappy length mismatch')
    return bytes(out)


def read_block(data, off, size):
    blk, ctype = data[off:off + size], data[off + size]
    if ctype == 1:
        return snappy_decompress(blk)
    if ctype == 0:
        return blk
    raise ValueError('unknown block compression %d' % ctype)


def block_entries(blk):
    nrest = struct.unpack('<I', blk[-4:])[0]
    end = len(blk) - 4 - 4 * nrest
    i, key = 0, b''
    while i < end:
        shared, i = varint(blk, i); nonsh, i = varint(blk, i); vl, i = varint(blk, i)
        key = key[:shared] + blk[i:i + nonsh]; i += nonsh
        yield key, blk[i:i + vl]; i += vl


def ldb_records(path):
    data = open(path, 'rb').read()
    if data[-8:] != b'\x57\xfb\x80\x8b\x24\x75\x47\xdb':
        raise ValueError('bad table magic')
    f = data[-48:]
    _, j = varint(f, 0); _, j = varint(f, j)           # metaindex handle
    ioff, j = varint(f, j); isz, j = varint(f, j)       # index handle
    for _, h in block_entries(read_block(data, ioff, isz)):
        boff, k = varint(h, 0); bsz, k = varint(h, k)
        for ikey, val in block_entries(read_block(data, boff, bsz)):
            tag = int.from_bytes(ikey[-8:], 'little')
            yield ikey[:-8], tag >> 8, tag & 0xff, val    # user key, seq, type (1=put, 0=del)


def log_records(path):
    data = open(path, 'rb').read(); recs = []; buf = b''
    for off in range(0, len(data), 32768):
        blk = data[off:off + 32768]; p = 0
        while p + 7 <= len(blk):
            ln, typ = struct.unpack('<HB', blk[p + 4:p + 7])
            if typ == 0 and ln == 0:
                break
            frag = blk[p + 7:p + 7 + ln]; p += 7 + ln
            if typ == 1: recs.append(frag)
            elif typ == 2: buf = frag
            elif typ == 3: buf += frag
            elif typ == 4: buf += frag; recs.append(buf); buf = b''
    for rec in recs:
        seq = struct.unpack('<Q', rec[:8])[0]; n = struct.unpack('<I', rec[8:12])[0]; i = 12
        for k in range(n):
            typ = rec[i]; i += 1
            kl, i = varint(rec, i); key = rec[i:i + kl]; i += kl
            val = b''
            if typ == 1:
                vl, i = varint(rec, i); val = rec[i:i + vl]; i += vl
            yield key, seq + k, typ, val


def load_diary(ldb_dir):
    best = None   # (seq, type, value, source)
    for f in sorted(glob.glob(os.path.join(ldb_dir, '*.ldb')) + glob.glob(os.path.join(ldb_dir, '*.log'))):
        try:
            recs = ldb_records(f) if f.endswith('.ldb') else log_records(f)
            for key, seq, typ, val in recs:
                if key.endswith(KEY_SUFFIX) and (best is None or seq > best[0]):
                    best = (seq, typ, val, os.path.basename(f))
        except Exception as e:
            die('could not decode %s: %s' % (os.path.basename(f), e))
    if best is None:
        die('amadeus_diary_v1 not found in localStorage')
    seq, typ, val, src = best
    if typ != 1:
        die('amadeus_diary_v1 was DELETED (seq %d, %s)' % (seq, src))
    txt = val[1:].decode('utf-16-le') if val[:1] == b'\x00' else val[1:].decode('latin-1')
    return json.loads(txt), src, seq


def chroma_docs(path):
    db = sqlite3.connect('file:%s?mode=ro' % path, uri=True)
    cid = [r[0] for r in db.execute("select id from collections where name='amadeus_diary'")]
    if not cid:
        die('collection amadeus_diary not found')
    return set((r[0] or '').strip() for r in db.execute(
        """select m.string_value from embedding_metadata m join embeddings e on e.id=m.id
           join segments s on s.id=e.segment_id where s.collection=? and m.key='chroma:document'""", (cid[0],)))


def main():
    if subprocess.run(['pgrep', '-x', 'Amadeus'], capture_output=True).returncode == 0:
        die('Amadeus is running — close it first (its files are being written)')
    chroma_arg = sys.argv[sys.argv.index('--chroma-copy') + 1] if '--chroma-copy' in sys.argv else None
    tmp = tempfile.mkdtemp(prefix='amadeus-diarycheck-')
    try:
        shutil.copytree(LS_DIR, os.path.join(tmp, 'ldb'))
        cpath = chroma_arg or os.path.join(tmp, 'chroma.sqlite3')
        if not chroma_arg:
            shutil.copy2(CHROMA, cpath)
        entries, src, seq = load_diary(os.path.join(tmp, 'ldb'))
        docs = chroma_docs(cpath)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not isinstance(entries, list) or not entries:
        die('diary decoded but empty or not a list')
    miss = [e for e in entries if (e.get('text') or '').strip() not in docs]
    print('localStorage diary: %d entries (from %s, seq %d) | newest: %s %s'
          % (len(entries), src, seq, entries[0].get('date'), entries[0].get('time', '')))
    print('ChromaDB amadeus_diary: %d documents | entries MISSING: %d' % (len(docs), len(miss)))
    for e in miss:
        print('  missing: %s %s — %s' % (e.get('date'), e.get('time', ''), (e.get('text') or '')[:70]))
    sys.exit(3 if miss else 0)


if __name__ == '__main__':
    main()
