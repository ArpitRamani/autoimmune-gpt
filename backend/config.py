import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

# Which provider writes the answers: "gemini" or "anthropic".
# Embeddings always use Gemini (Anthropic has no embedding model).
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "gemini").strip().lower()

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash").strip()
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004").strip()
ANTHROPIC_CHAT_MODEL = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-haiku-4-5").strip()

PAPERS_DIR = PROJECT_ROOT / "data" / "papers"
STORE_DIR = Path(__file__).resolve().parent / "store"
VECTORS_PATH = STORE_DIR / "vectors.npz"
CHUNKS_PATH = STORE_DIR / "chunks.json"

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
