#!/usr/bin/env python3
"""
One-shot ingestion: reads both Kurisu corpora and builds two ChromaDB collections.

Collections:
  kurisu_ja  — 756 Japanese voice-clip transcripts  (tonal anchors)
  kurisu_en  — 1672 English LP dialogue lines        (style examples)

Run once:  /opt/homebrew/bin/python3 build_kurisu_index.py
ChromaDB persisted to: ~/Documents/Amadeus/data/chroma/
"""

import csv
import os
import sys
import time
import requests

# ── paths ────────────────────────────────────────────────────────────────────
AMADEUS_DIR   = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR    = os.path.join(AMADEUS_DIR, 'data', 'chroma')
JA_CSV        = os.path.expanduser('~/Documents/Kurisu_Dataset_Pro/metadata.csv')
EN_CSV        = os.path.expanduser('~/Desktop/kurisu_english_lines.csv')
EMBED_MODEL   = 'bge-m3'
OLLAMA_URL    = 'http://127.0.0.1:11434/api/embed'
BATCH_SIZE    = 50   # lines per Ollama embed call

os.makedirs(CHROMA_DIR, exist_ok=True)

# ── chromadb ─────────────────────────────────────────────────────────────────
import chromadb
client = chromadb.PersistentClient(path=CHROMA_DIR)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via Ollama bge-m3. Returns list of embedding vectors."""
    resp = requests.post(OLLAMA_URL, json={'model': EMBED_MODEL, 'input': texts}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    # Ollama /api/embed returns {"embeddings": [[...], ...]}
    return data['embeddings']


def ingest_collection(name: str, ids: list[str], docs: list[str], metadatas: list[dict]):
    """Drop-and-recreate collection, embed in batches, upsert."""
    # Delete existing collection so re-runs are idempotent
    try:
        client.delete_collection(name)
        print(f'[{name}] Dropped existing collection.')
    except Exception:
        pass

    col = client.create_collection(name, metadata={'hnsw:space': 'cosine'})
    total = len(docs)
    print(f'[{name}] Ingesting {total} documents in batches of {BATCH_SIZE}…')

    inserted = 0
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_ids  = ids[start:end]
        batch_docs = docs[start:end]
        batch_meta = metadatas[start:end]

        embeddings = embed_batch(batch_docs)
        col.add(ids=batch_ids, embeddings=embeddings, documents=batch_docs, metadatas=batch_meta)
        inserted += len(batch_ids)
        if inserted % 100 == 0 or inserted == total:
            print(f'  [{name}] {inserted}/{total}')

    print(f'[{name}] Done. {col.count()} documents stored.')
    return col


# ── load Japanese corpus ──────────────────────────────────────────────────────
print('=== Loading Japanese corpus ===')
ja_ids, ja_docs, ja_meta = [], [], []
with open(JA_CSV, encoding='utf-8-sig', newline='') as f:
    # No header row; pipe-separated: filename|japanese_transcript
    reader = csv.reader(f, delimiter='|', quoting=csv.QUOTE_NONE)
    for row in reader:
        if len(row) < 2:
            continue
        filename, transcript = row[0].strip(), row[1].strip()
        if not transcript:
            continue
        stem = os.path.splitext(filename)[0]   # e.g. kurisu_0000
        ja_ids.append(stem)
        ja_docs.append(transcript)
        ja_meta.append({'lang': 'ja', 'clip_id': stem})

print(f'  Loaded {len(ja_docs)} Japanese lines.')


# ── load English corpus ───────────────────────────────────────────────────────
print('=== Loading English corpus ===')
en_ids, en_docs, en_meta = [], [], []
with open(EN_CSV, encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)  # has header: update,line
    for i, row in enumerate(reader):
        line = row.get('line', '').strip()
        if not line:
            continue
        update_num = int(row.get('update', 0))
        en_ids.append(f'en_{i}')
        en_docs.append(line)
        en_meta.append({'lang': 'en', 'update': update_num})

print(f'  Loaded {len(en_docs)} English lines.')


# ── ingest both ───────────────────────────────────────────────────────────────
t0 = time.time()
ingest_collection('kurisu_ja', ja_ids, ja_docs, ja_meta)
ingest_collection('kurisu_en', en_ids, en_docs, en_meta)
elapsed = time.time() - t0

# ── report ────────────────────────────────────────────────────────────────────
import shutil
chroma_mb = sum(
    os.path.getsize(os.path.join(dp, f))
    for dp, _, files in os.walk(CHROMA_DIR)
    for f in files
) / (1024 * 1024)

print(f'\n=== Ingestion complete in {elapsed:.1f}s ===')
print(f'  kurisu_ja: {client.get_collection("kurisu_ja").count()} docs')
print(f'  kurisu_en: {client.get_collection("kurisu_en").count()} docs')
print(f'  ChromaDB size on disk: {chroma_mb:.1f} MB  ({CHROMA_DIR})')
