"""Fetch web pages (e.g. the association's site), extract just the main article
text, and turn them into chunks for the index — same shape as the PDF chunks."""
import re
import urllib.request
from typing import Dict, List

import trafilatura

import config

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def load_urls() -> List[str]:
    if not config.URLS_PATH.exists():
        return []
    urls = []
    for line in config.URLS_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def _fetch_html(url: str) -> str | None:
    html = trafilatura.fetch_url(url)
    if html:
        return html
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception:
        return None


def _window(text: str, source: str) -> List[Dict]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    chunks: List[Dict] = []
    start, section = 0, 1
    while start < len(text):
        end = start + config.CHUNK_SIZE
        piece = text[start:end].strip()
        if len(piece) >= 40:
            chunks.append({"text": piece, "source": source, "page": section})
            section += 1
        if end >= len(text):
            break
        start = end - config.CHUNK_OVERLAP
    return chunks


def load_web_chunks() -> List[Dict]:
    """Fetch every URL in data/urls.txt and return clean-text chunks."""
    all_chunks: List[Dict] = []
    for url in load_urls():
        print(f"Fetching {url} ...", end=" ", flush=True)
        html = _fetch_html(url)
        if not html:
            print("could not fetch — skipped")
            continue
        text = trafilatura.extract(html, include_comments=False, include_tables=True)
        if not text or len(text) < 200:
            print("no usable text — skipped")
            continue
        chunks = _window(text, source=url)
        all_chunks.extend(chunks)
        print(f"{len(text)} chars -> {len(chunks)} chunks")
    return all_chunks
