# Autoimmune Research Assistant

A small, low-cost chatbot that lets patients and caregivers ask questions and get answers
**grounded only in a curated library of research papers** — not the open internet, and not the
model's own memory. Built on Gemini Flash (chat) + Gemini embeddings (retrieval).

This is a **RAG** (Retrieval-Augmented Generation) system:

```
PDFs you curate  ──►  ingest.py  ──►  text chunks + embeddings  (stored locally)
                                              │
  patient question ──► embed ──► find most relevant chunks ──► Gemini Flash ──► grounded answer + citations
```

Because the model is instructed to answer **only** from the retrieved chunks, it can't wander
off into unvetted claims, and every answer comes with the source paper + page.

---

## Setup (one time)

```bash
cd autoimmune-research-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and paste your free key from https://aistudio.google.com/apikey
```

## Add your research

Drop the PDFs you want the assistant to use into:

```
data/papers/
```

Then build the index (re-run this whenever you add/remove papers):

```bash
python backend/ingest.py
```

## Run it

```bash
uvicorn backend.server:app --reload --port 8000
```

Open **http://localhost:8000** and start asking questions.

---

## Cost

Roughly, for a small library:
- **Embedding** the papers: a one-time cost, fractions of a cent per paper.
- **Each question**: one small embedding call + one Gemini Flash call — well under a cent each.

Gemini Flash is one of the cheapest capable models available, which is why it fits a
patient-facing, possibly-high-volume tool.

## Safety design

This is a patient-facing medical tool, so guardrails are built in:
- The model is constrained to the curated library and told to say "this isn't covered" rather than guess.
- It is instructed never to diagnose or recommend specific treatments/doses, and to defer to a clinician.
- A persistent on-screen disclaimer states it is educational, not medical advice.
- Every answer shows its sources for verification.

These reduce risk but do not eliminate it. Before any public launch, have a clinician/compliance
reviewer sign off, and confirm you have the rights to use the papers you ingest.

## Project layout

```
backend/
  config.py         settings + paths (chunk size, top-k, models)
  gemini_client.py  Gemini SDK wrapper (embeddings + chat, batching + retries)
  ingest.py         PDF -> chunks -> embeddings -> local index
  rag.py            retrieval + grounded answer generation
  server.py         FastAPI: serves the page + /api/chat
frontend/
  index.html        the chat page
data/papers/        <- you put PDFs here
```
