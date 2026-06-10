"use client";

import { useEffect, useRef, useState } from "react";

type Source = {
  n: number;
  source: string;
  page: number;
  score: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  pending?: boolean;
};

const GREETING: Message = {
  role: "assistant",
  content:
    "Hi! I answer questions using a curated library of autoimmune research. Ask me anything about the studies in the collection.",
};

const SUGGESTIONS = [
  "What does the research say about diet and inflammation?",
  "Are there findings on stress and flare-ups?",
  "Summarize what's known about gut health and autoimmunity.",
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;

    setMessages((m) => [
      ...m,
      { role: "user", content: question },
      { role: "assistant", content: "", pending: true },
    ]);
    setInput("");
    setBusy(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const data = await res.json();
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: data.answer ?? "(no answer)",
          sources: data.sources ?? [],
        };
        return next;
      });
    } catch {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: "Something went wrong reaching the server.",
        };
        return next;
      });
    } finally {
      setBusy(false);
      taRef.current?.focus();
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  const showSuggestions = messages.length === 1;

  return (
    <div className="mx-auto flex h-[100dvh] w-full max-w-3xl flex-col px-4 py-4 sm:py-6">
      <div className="flex flex-1 flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-200/60">
        <Header />
        <Disclaimer />

        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-4 py-6 sm:px-6">
          {messages.map((m, i) => (
            <Bubble key={i} message={m} />
          ))}

          {showSuggestions && (
            <div className="flex flex-wrap gap-2 pt-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm text-slate-600 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-slate-100 bg-white/70 px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 focus-within:border-sky-400 focus-within:ring-2 focus-within:ring-sky-100">
            <textarea
              ref={taRef}
              rows={1}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px";
              }}
              onKeyDown={onKeyDown}
              placeholder="Ask about the research…"
              className="max-h-36 flex-1 resize-none bg-transparent py-1.5 text-[15px] leading-relaxed text-slate-800 placeholder:text-slate-400 focus:outline-none"
            />
            <button
              onClick={() => send(input)}
              disabled={busy || !input.trim()}
              className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-sky-600 text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send"
            >
              <SendIcon />
            </button>
          </div>
          <p className="mt-2 px-1 text-center text-xs text-slate-400">
            Educational use only — not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}

function Header() {
  return (
    <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-sky-500 to-indigo-500 text-lg">
        🧬
      </div>
      <div>
        <h1 className="text-[15px] font-semibold text-slate-800">Autoimmune Research Assistant</h1>
        <p className="text-xs text-slate-500">Grounded in a curated research library</p>
      </div>
    </div>
  );
}

function Disclaimer() {
  return (
    <div className="border-b border-amber-100 bg-amber-50 px-5 py-2.5 text-xs leading-relaxed text-amber-800 sm:px-6">
      ⚠️ This tool summarizes published research for educational purposes only. It is not medical
      advice. Always discuss your care with a qualified healthcare provider.
    </div>
  );
}

function Bubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  if (message.pending) {
    return (
      <div className="flex justify-start">
        <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3">
          <span className="flex items-center gap-1 text-slate-400">
            <span className="dot h-2 w-2 rounded-full bg-slate-400" />
            <span className="dot h-2 w-2 rounded-full bg-slate-400" />
            <span className="dot h-2 w-2 rounded-full bg-slate-400" />
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[82%] rounded-2xl rounded-br-md bg-gradient-to-br from-sky-600 to-indigo-600 px-4 py-3 text-[15px] leading-relaxed text-white shadow-sm"
            : "max-w-[82%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-[15px] leading-relaxed text-slate-800 shadow-sm"
        }
      >
        <div className="whitespace-pre-wrap">{renderWithCitations(message.content)}</div>
        {message.sources && message.sources.length > 0 && <Sources sources={message.sources} />}
      </div>
    </div>
  );
}

function Sources({ sources }: { sources: Source[] }) {
  return (
    <div className="mt-3 border-t border-dashed border-slate-200 pt-2.5">
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">Sources</p>
      <div className="flex flex-col gap-1.5">
        {sources.map((s) => (
          <div key={s.n} className="flex items-center gap-2 text-xs text-slate-500">
            <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-slate-100 text-[10px] font-semibold text-slate-600">
              {s.n}
            </span>
            <span className="truncate">{s.source}</span>
            <span className="shrink-0 text-slate-400">· p.{s.page}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function renderWithCitations(text: string) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (m) {
      return (
        <sup
          key={i}
          className="mx-0.5 rounded bg-slate-100 px-1 text-[10px] font-semibold text-slate-500"
        >
          {m[1]}
        </sup>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 2 11 13" />
      <path d="M22 2 15 22l-4-9-9-4 20-7Z" />
    </svg>
  );
}
