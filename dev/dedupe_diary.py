#!/usr/bin/env python3
"""
dedupe_diary.py — ONE-OFF migration for the amadeus_diary duplication bug.

The bug (kurisu_rag_server.py /index-diary): entries sharing a date got an id
from their POSITION in the array. New entries are unshift()ed to the front, so
every position shifts by one on each write, and upsert under a shifted id
created a NEW row instead of updating. Result: 79 rows, 55 unique, one entry
stored 5 times -- and retrieval weights a memory by how many copies exist.

This re-keys every row to a content-derived id and drops the redundant copies,
so the collection matches what the fixed server will write.

DEFAULT IS DRY RUN. Nothing is written without --apply.
--apply backs up chroma.sqlite3 first and refuses to run without a backup.

Entries that exist only in Chroma (aged out of the 50-entry localStorage diary)
are PRESERVED -- the collection is deliberately a superset, and deleting them
would lose real history.

  python3 dev/dedupe_diary.py                 # report only
  python3 dev/dedupe_diary.py --db PATH       # run against a copy
  python3 dev/dedupe_diary.py --apply         # migrate for real (app must be closed)
"""
import argparse, hashlib, os, shutil, sys, time
from collections import defaultdict

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'data', 'chroma')
COLLECTION = 'amadeus_diary'


def stable_id(text: str) -> str:
    """Content-derived id. Must match kurisu_rag_server.py exactly, or the next
    index pass re-inserts everything under different ids."""
    return 'd' + hashlib.sha1(text.strip().encode('utf-8')).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--prune', metavar='JSON',
                    help='file from rewriteClinicalDiary(): delete the rows it replaced')
    a = ap.parse_args()

    import chromadb
    client = chromadb.PersistentClient(path=a.db)
    col = client.get_collection(COLLECTION)

    if a.prune:
        # Delete exactly the rows whose text the in-app cleanup replaced. Ids are
        # recomputed here with the SAME stable_id() the server uses, so this can
        # never touch a row that was not on the list.
        import json
        texts = json.load(open(os.path.expanduser(a.prune)))['replaced']
        want = [stable_id(t) for t in texts if (t or '').strip()]
        present = set(col.get(include=[])['ids'])
        hit = [i for i in want if i in present]
        print(f'  rows now       {col.count()}')
        print(f'  replaced texts {len(want)}   present in db {len(hit)}')
        if not a.apply:
            print('\nDRY RUN — nothing written. Add --apply to delete them.')
            return
        sqlite = os.path.join(a.db, 'chroma.sqlite3')
        backup = f'{sqlite}.bak-{time.strftime("%Y%m%d-%H%M%S")}'
        shutil.copy2(sqlite, backup)
        if os.path.getsize(backup) != os.path.getsize(sqlite):
            print('BACKUP FAILED — refusing to modify anything.'); sys.exit(1)
        print(f'  backup written {backup}')
        if hit:
            col.delete(ids=hit)
        print(f'  deleted        {len(hit)}')
        print(f'  rows now       {col.count()}')
        return
    g = col.get(include=['documents', 'metadatas'])
    ids, docs, metas = g['ids'], g['documents'], g['metadatas']

    by_text = defaultdict(list)
    for i, d, m in zip(ids, docs, metas or [{}] * len(ids)):
        by_text[(d or '').strip()].append((i, m or {}))

    keep, drop = {}, []
    for text, rows in by_text.items():
        if not text:
            drop.extend(r[0] for r in rows)
            continue
        # keep the row with the richest metadata (a real date beats a positional id)
        rows.sort(key=lambda r: (bool(r[1].get('date')), r[0]), reverse=True)
        keep[text] = rows[0]
        drop.extend(r[0] for r in rows[1:])

    rekey = [(old_id, stable_id(t), t, m) for t, (old_id, m) in keep.items()
             if old_id != stable_id(t)]

    print(f'db         {a.db}')
    print(f'collection {COLLECTION}')
    print(f'  rows now            {len(ids)}')
    print(f'  unique texts        {len(keep)}')
    print(f'  redundant copies    {len(drop)}   ({100*len(drop)/max(1,len(ids)):.0f}% of the collection)')
    print(f'  rows to re-key      {len(rekey)}')
    print(f'  rows after          {len(keep)}')
    if not a.apply:
        print('\nDRY RUN — nothing written. Re-run with --apply to migrate.')
        worst = sorted(by_text.items(), key=lambda kv: -len(kv[1]))[:3]
        print('\nworst duplicates:')
        for t, rows in worst:
            if len(rows) > 1:
                print(f'  x{len(rows)}  {t[:70]}...')
        return

    # --apply: back up first, and refuse if the backup fails.
    sqlite = os.path.join(a.db, 'chroma.sqlite3')
    backup = f'{sqlite}.bak-{time.strftime("%Y%m%d-%H%M%S")}'
    shutil.copy2(sqlite, backup)
    if not os.path.exists(backup) or os.path.getsize(backup) != os.path.getsize(sqlite):
        print('BACKUP FAILED — refusing to modify anything.'); sys.exit(1)
    print(f'  backup written      {backup}')

    # Re-key by ADD-then-DELETE so a crash mid-way loses nothing:
    # the new row exists before the old one is removed.
    if rekey:
        embs = col.get(ids=[r[0] for r in rekey], include=['embeddings'])['embeddings']
        col.upsert(ids=[r[1] for r in rekey], embeddings=embs,
                   documents=[r[2] for r in rekey], metadatas=[r[3] for r in rekey])
        print(f'  re-keyed            {len(rekey)}')
        drop.extend(r[0] for r in rekey)

    if drop:
        col.delete(ids=list(dict.fromkeys(drop)))
        print(f'  deleted             {len(set(drop))}')

    print(f'\n  rows now            {col.count()}   (expected {len(keep)})')
    assert col.count() == len(keep), 'COUNT MISMATCH — restore from the backup above'
    print('  OK — every unique entry preserved, duplicates removed.')


if __name__ == '__main__':
    main()
