"""Fetch web pages (e.g. the association's site), extract just the main article
text, and turn them into chunks for the index — same shape as the PDF chunks."""
import re
import ssl
import urllib.request
from typing import Dict, List

import certifi
import trafilatura

import config

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_CTX = ssl.create_default_context(cafile=certifi.where())


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
        with urllib.request.urlopen(req, timeout=30, context=_CTX) as resp:
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


def _fetch_and_chunk(url: str) -> List[Dict]:
    html = _fetch_html(url)
    if not html:
        return []
    text = trafilatura.extract(html, include_comments=False, include_tables=True)
    if not text or len(text) < 200:
        return []
    return _window(text, source=url)


def load_web_chunks(max_workers: int = 8) -> List[Dict]:
    """Fetch every URL in data/urls.txt (concurrently) and return clean-text chunks."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    urls = load_urls()
    if not urls:
        return []
    print(f"Fetching {len(urls)} web page(s) with {max_workers} workers ...")
    all_chunks: List[Dict] = []
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_and_chunk, u): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            chunks = fut.result()
            if chunks:
                all_chunks.extend(chunks)
                ok += 1
            else:
                fail += 1
            if i % 50 == 0 or i == len(urls):
                print(f"  {i}/{len(urls)} done ({ok} ok, {fail} empty/failed, {len(all_chunks)} chunks)")
    return all_chunks
