"""Build the search index from the PDFs in data/papers/. Re-run after changing papers."""
import json
import re
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
from pypdf import PdfReader

import config
from gemini_client import embed_texts


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
    config.require_api_key()
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(config.PAPERS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {config.PAPERS_DIR}")
        print("Drop your curated research papers there and re-run this script.")
        return 1

    all_chunks: List[Dict] = []
    for pdf in pdfs:
        print(f"Reading {pdf.name} ...", end=" ", flush=True)
        pages = extract_pages(pdf)
        chunks = chunk_pages(pages, source=pdf.name)
        all_chunks.extend(chunks)
        print(f"{len(pages)} pages -> {len(chunks)} chunks")

    if not all_chunks:
        print("Extracted 0 usable chunks. Are these scanned (image-only) PDFs?")
        return 1

    print(f"\nEmbedding {len(all_chunks)} chunks with {config.EMBED_MODEL} ...")
    vectors = embed_texts([c["text"] for c in all_chunks], task_type="RETRIEVAL_DOCUMENT")
    matrix = np.array(vectors, dtype=np.float32)
    matrix /= (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)

    np.savez_compressed(config.VECTORS_PATH, vectors=matrix)
    config.CHUNKS_PATH.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2))

    print(f"\nDone. Indexed {len(all_chunks)} chunks from {len(pdfs)} paper(s).")
    print(f"  vectors -> {config.VECTORS_PATH}")
    print(f"  chunks  -> {config.CHUNKS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
