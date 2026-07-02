"""Build the search index from the PDFs in data/papers/. Re-run after changing papers."""
import json
import re
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
from pypdf import PdfReader

import config
from embeddings import embed_texts
from web_sources import load_web_chunks


def extract_pages(pdf_path: Path) -> List[str]:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(_clean(text))
    return pages


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_pages(pages: List[str], source: str) -> List[Dict]:
    chunks: List[Dict] = []
    for page_num, page_text in enumerate(pages, start=1):
        if len(page_text) < 40:
            continue
        start = 0
        while start < len(page_text):
            end = start + config.CHUNK_SIZE
            piece = page_text[start:end].strip()
            if len(piece) >= 40:
                chunks.append({
                    "text": piece,
                    "source": source,
                    "page": page_num,
                })
            if end >= len(page_text):
                break
            start = end - config.CHUNK_OVERLAP
    return chunks


def main() -> int:
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks: List[Dict] = []

    # 1. PDFs in data/papers/
    pdfs = sorted(config.PAPERS_DIR.glob("*.pdf"))
    for pdf in pdfs:
        print(f"Reading {pdf.name} ...", end=" ", flush=True)
        pages = extract_pages(pdf)
        chunks = chunk_pages(pages, source=pdf.name)
        all_chunks.extend(chunks)
        print(f"{len(pages)} pages -> {len(chunks)} chunks")

    # 2. Web pages listed in data/urls.txt
    web_chunks = load_web_chunks()
    all_chunks.extend(web_chunks)

    if not all_chunks:
        print("Nothing to index. Add PDFs to data/papers/ or URLs to data/urls.txt.")
        return 1

    print(f"\nEmbedding {len(all_chunks)} chunks with {config.embed_signature()} ...")
    vectors = embed_texts([c["text"] for c in all_chunks], task_type="RETRIEVAL_DOCUMENT")
    matrix = np.array(vectors, dtype=np.float32)
    matrix /= (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)

    np.savez_compressed(config.VECTORS_PATH, vectors=matrix)
    config.CHUNKS_PATH.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2))
    config.META_PATH.write_text(json.dumps({
        "embed_signature": config.embed_signature(),
        "dim": int(matrix.shape[1]),
        "chunks": len(all_chunks),
    }, indent=2))

    n_web = len({c["source"] for c in web_chunks})
    print(f"\nDone. Indexed {len(all_chunks)} chunks from {len(pdfs)} paper(s) + {n_web} web page(s).")
    print(f"  vectors -> {config.VECTORS_PATH}")
    print(f"  chunks  -> {config.CHUNKS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
