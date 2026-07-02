"""Discover page URLs from a site's sitemap and write them to data/urls.txt.

    python backend/discover.py                      # defaults to autoimmune.org
    python backend/discover.py https://site/sitemap_index.xml
"""
import re
import ssl
import sys
import urllib.request
from typing import List

import certifi

import config

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_CTX = ssl.create_default_context(cafile=certifi.where())
_DEFAULT = "https://autoimmune.org/sitemap_index.xml"

# Skip non-article URLs (media, feeds, etc.)
_SKIP = re.compile(r"\.(jpg|jpeg|png|gif|webp|svg|pdf|zip)$|/feed/?$|/wp-json", re.I)


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as resp:
        return resp.read().decode("utf-8", "ignore")


def _locs(xml: str) -> List[str]:
    return [m.strip() for m in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)]


def discover(sitemap_url: str) -> List[str]:
    xml = _fetch(sitemap_url)
    locs = _locs(xml)
    # A sitemap index points to child sitemaps; expand those one level.
    child_sitemaps = [u for u in locs if u.endswith(".xml")]
    pages: List[str] = [u for u in locs if not u.endswith(".xml")]
    for child in child_sitemaps:
        try:
            print(f"  reading {child} ...", end=" ", flush=True)
            page_urls = [u for u in _locs(_fetch(child)) if not u.endswith(".xml")]
            pages.extend(page_urls)
            print(f"{len(page_urls)} urls")
        except Exception as e:
            print(f"skipped ({e})")
    # dedupe + filter
    seen, out = set(), []
    for u in pages:
        if u not in seen and not _SKIP.search(u):
            seen.add(u)
            out.append(u)
    return out


def main() -> int:
    sitemap = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT
    print(f"Discovering from {sitemap}")
    urls = discover(sitemap)
    header = "# Auto-discovered from the sitemap. Re-run: python backend/discover.py\n"
    config.URLS_PATH.write_text(header + "\n".join(urls) + "\n")
    print(f"\nWrote {len(urls)} URLs -> {config.URLS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
