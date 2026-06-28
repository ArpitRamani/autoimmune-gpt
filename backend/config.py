import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

# Which provider writes the answers: "anthropic" (default) or "gemini".
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "anthropic").strip().lower()
ANTHROPIC_CHAT_MODEL = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-haiku-4-5").strip()
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash").strip()

# Which provider does the embeddings/retrieval: "local" (default, no key) or "gemini".
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "local").strip().lower()
LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "BAAI/bge-small-en-v1.5").strip()
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004").strip()


def embed_signature() -> str:
    """Identifies how the index was embedded, so retrieval can detect a mismatch."""
    model = GEMINI_EMBED_MODEL if EMBED_PROVIDER == "gemini" else LOCAL_EMBED_MODEL
    return f"{EMBED_PROVIDER}:{model}"


PAPERS_DIR = PROJECT_ROOT / "data" / "papers"
STORE_DIR = Path(__file__).resolve().parent / "store"
VECTORS_PATH = STORE_DIR / "vectors.npz"
CHUNKS_PATH = STORE_DIR / "chunks.json"
META_PATH = STORE_DIR / "meta.json"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
TOP_K = 6
MIN_SCORE = 0.45


def require_api_key() -> str:
    if not GEMINI_API_KEY:
        raise SystemExit(
            "GEMINI_API_KEY is not set.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Paste your key from https://aistudio.google.com/apikey\n"
        )
    return GEMINI_API_KEY


def require_anthropic_key() -> str:
    if not ANTHROPIC_API_KEY:
        raise SystemExit(
            "CHAT_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.\n"
            "  Paste your key from https://console.anthropic.com/ into .env\n"
        )
    return ANTHROPIC_API_KEY
