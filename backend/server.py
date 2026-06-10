import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag import RagEngine

app = FastAPI(title="Autoimmune Research Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: RagEngine | None = None


def engine() -> RagEngine:
    global _engine
    if _engine is None:
        _engine = RagEngine()
    return _engine


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    question = (req.message or "").strip()
    if not question:
        return {"answer": "Please type a question.", "sources": []}
    result = engine().answer(question)
    return {
        "answer": result.text,
        "sources": [
            {"n": s.n, "source": s.source, "page": s.page, "score": round(s.score, 3)}
            for s in result.sources
        ],
    }


@app.get("/api/health")
def health():
    return {"ok": True}
