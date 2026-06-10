import json
from dataclasses import dataclass
from typing import List, Dict

import numpy as np

import config
from gemini_client import embed_texts
from llm import generate

SYSTEM_PROMPT = """You are a research-access assistant for the autoimmune patient community.
Your job is to help patients and caregivers understand published research.

STRICT RULES — follow every one:
1. Answer ONLY using the numbered SOURCES provided in the user message. Treat them as
   your entire knowledge. Do not use outside knowledge or fill gaps from memory.
2. If the sources do not contain the answer, say so plainly:
   "The research in this library doesn't cover that." Do not guess.
3. Cite the sources you used inline like [1], [2] after the relevant sentence.
4. You are NOT a doctor. Never diagnose, never recommend a specific treatment, dose,
   or change to someone's care. Explain what the research says, in plain language.
5. For anything about an individual's own treatment decisions, add one sentence telling
   them to discuss it with their own healthcare provider.
6. Write clearly and warmly for a non-expert. Define jargon the first time you use it.

Keep answers focused and readable. Use short paragraphs or bullet points."""


@dataclass
class Source:
    n: int
    source: str
    page: int
    score: float
    text: str


@dataclass
class Answer:
    text: str
    sources: List[Source]


class RagEngine:
    def __init__(self):
        if not config.VECTORS_PATH.exists() or not config.CHUNKS_PATH.exists():
            raise SystemExit(
                "Index not found. Add PDFs to data/papers/ and run:\n"
                "    python backend/ingest.py\n"
            )
        self.matrix = np.load(config.VECTORS_PATH)["vectors"]
        self.chunks: List[Dict] = json.loads(config.CHUNKS_PATH.read_text())

    def retrieve(self, question: str) -> List[Source]:
        q = embed_texts([question], task_type="RETRIEVAL_QUERY")[0]
        qv = np.array(q, dtype=np.float32)
        qv /= (np.linalg.norm(qv) + 1e-12)
        scores = self.matrix @ qv
        top_idx = np.argsort(-scores)[: config.TOP_K]
        sources: List[Source] = []
        for rank, idx in enumerate(top_idx, start=1):
            score = float(scores[idx])
            if score < config.MIN_SCORE:
                continue
            c = self.chunks[idx]
            sources.append(Source(
                n=len(sources) + 1,
                source=c["source"],
                page=c["page"],
                score=score,
                text=c["text"],
            ))
        return sources

    def answer(self, question: str) -> Answer:
        sources = self.retrieve(question)
        if not sources:
            return Answer(
                text="The research in this library doesn't cover that. Try rephrasing, "
                     "or ask about a topic covered by the papers in the collection.",
                sources=[],
            )
        context = "\n\n".join(
            f"[{s.n}] (from {s.source}, p.{s.page})\n{s.text}" for s in sources
        )
        user_prompt = f"SOURCES:\n{context}\n\nQUESTION: {question}\n\nAnswer using only the sources above."
        text = generate(SYSTEM_PROMPT, user_prompt)
        return Answer(text=text, sources=sources)
