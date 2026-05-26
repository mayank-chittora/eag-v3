"""
memory.py — Typed memory service.

Three read methods (no LLM except relevant()), two write methods.
Persists to state/memory.json across runs.

Read cost profile:
  read()     → pure Python keyword overlap — used every iteration
  filter()   → pure Python structured filter
  relevant() → one LLM call — used only when keyword recall is weak

Write cost profile:
  remember()       → one LLM classification call (extracts kind/keywords/value)
  record_outcome() → no LLM — kind is tool_outcome by construction
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

from schemas import ActionEvent, AnswerEvent, HistoryEvent, MemoryItem, ToolCall

# Gateway client path
_GW = Path(__file__).parent / "llm_gatewayV3"
if str(_GW) not in sys.path:
    sys.path.insert(0, str(_GW))

from client import LLM  # noqa: E402


def _chat_with_retry(llm: LLM, prompt: str, max_retries: int = 3, **kwargs) -> dict:
    for attempt in range(max_retries):
        try:
            return llm.chat(prompt, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 502, 503) and attempt < max_retries - 1:
                wait = 10 * (2 ** attempt)
                print(f"  [memory] rate-limited ({e.response.status_code}), retrying in {wait}s ...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("unreachable")

_STATE_DIR = Path(__file__).parent / "state"
_MEMORY_PATH = _STATE_DIR / "memory.json"

_GEMINI = {"provider": "g", "model": "gemini-3.1-flash-lite"}

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "to", "of", "in", "on", "at", "for",
    "with", "from", "by", "about", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "or", "but",
    "if", "then", "that", "this", "i", "me", "my", "you", "your", "we",
    "our", "he", "she", "it", "they", "what", "when", "where", "how",
    "not", "no", "yes", "get", "give", "tell", "find", "show", "search",
    "check", "read", "list", "make", "create", "update", "edit", "can",
    "please", "want", "need", "help", "use", "using", "used", "also",
    "just", "up", "out", "so", "very", "now", "than", "then", "its",
    "which", "who", "whom", "there", "here", "all", "any", "each",
    "few", "more", "most", "other", "some", "such", "own", "same",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": ["fact", "preference", "tool_outcome", "scratchpad"],
        },
        "keywords": {"type": "array", "items": {"type": "string"}},
        "descriptor": {"type": "string"},
        "value": {"type": "object"},
        "confidence": {"type": "number"},
    },
    "required": ["kind", "keywords", "descriptor", "value", "confidence"],
}

_CLASSIFY_SYSTEM = """\
You are a memory classifier. Classify user text into a memory item.

kind rules:
  fact        — durable observed truths (dates, names, places, event facts)
  preference  — stated user preferences ("I prefer", "remind me", "I like")
  scratchpad  — run-scoped working notes or ambiguous intent
  tool_outcome — results from tool invocations (rarely used in remember())

Output rules:
  keywords: 3-8 lowercase tokens useful for future keyword search; no stopwords
  descriptor: one short human-readable summary line (max 100 chars)
  value: structured dict with extracted entities, e.g.
         {"entity": "mom", "attribute": "birthday", "value": "2026-05-15"}
  confidence: 0.0-1.0
"""


class MemoryService:
    def __init__(self, path: Path = _MEMORY_PATH) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[MemoryItem] = self._load()
        self._llm = LLM()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> list[MemoryItem]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [MemoryItem.model_validate(x) for x in raw.get("items", [])]
        except Exception:
            return []

    def _save(self) -> None:
        data = {"items": [item.model_dump(mode="json") for item in self._items]}
        self._path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    # ── Read methods ─────────────────────────────────────────────────────────

    def read(
        self,
        query: str,
        history: list[HistoryEvent],
        kinds: list[str] | None = None,
        top_k: int = 8,
    ) -> list[MemoryItem]:
        """Keyword overlap scoring — pure Python, no LLM. Called every iteration."""
        q_tokens = set(_tokenize(query))
        # Supplement with tokens from recent history descriptors
        for h in history[-6:]:
            if isinstance(h, ActionEvent):
                q_tokens.update(_tokenize(h.result_descriptor))
            elif isinstance(h, AnswerEvent):
                q_tokens.update(_tokenize(h.text))

        scored: list[tuple[int, MemoryItem]] = []
        for item in self._items:
            if kinds and item.kind not in kinds:
                continue
            item_tokens = set(item.keywords) | set(_tokenize(item.descriptor))
            overlap = len(q_tokens & item_tokens)
            if overlap > 0:
                scored.append((overlap, item))

        scored.sort(key=lambda x: (-x[0], x[1].created_at.isoformat()))
        return [item for _, item in scored[:top_k]]

    def filter(
        self,
        kinds: list[str] | None = None,
        goal_id: str | None = None,
        recent: int | None = None,
    ) -> list[MemoryItem]:
        """Structured filter — pure Python, no LLM."""
        items = list(self._items)
        if kinds:
            items = [x for x in items if x.kind in kinds]
        if goal_id:
            items = [x for x in items if x.goal_id == goal_id]
        if recent:
            items = items[-recent:]
        return items

    def relevant(
        self,
        query: str,
        kinds: list[str] | None = None,
        top_k: int = 5,
    ) -> list[MemoryItem]:
        """LLM-scored relevance — use only when keyword recall is weak."""
        candidates = self.filter(kinds=kinds, recent=50)
        if not candidates:
            return []
        lines = [f"{i}: {c.descriptor}" for i, c in enumerate(candidates)]
        prompt = (
            f"Query: {query}\n\nCandidates:\n" + "\n".join(lines)
            + "\n\nReturn indices of top relevant items as JSON: {\"indices\": [0, 1, ...]}"
        )
        try:
            resp = _chat_with_retry(
                self._llm,
                prompt,
                **_GEMINI,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=128,
            )
            data = json.loads(resp.get("text", "{}"))
            indices = data.get("indices", [])
            return [candidates[i] for i in indices if 0 <= i < len(candidates)][:top_k]
        except Exception:
            return candidates[:top_k]

    # ── Write methods ─────────────────────────────────────────────────────────

    def remember(
        self,
        raw_text: str,
        *,
        source: str,
        run_id: str,
        goal_id: str | None = None,
    ) -> MemoryItem:
        """LLM classification. Extracts kind/keywords/descriptor/value from raw text."""
        try:
            resp = _chat_with_retry(
                self._llm,
                raw_text,
                system=_CLASSIFY_SYSTEM,
                **_GEMINI,
                response_format={"type": "json_schema", "schema": _CLASSIFY_SCHEMA},
                temperature=0.0,
                max_tokens=512,
            )
            data = resp.get("parsed") or json.loads(resp.get("text", "{}"))
        except Exception as e:
            # Fallback: minimal scratchpad entry so the agent can continue
            data = {
                "kind": "scratchpad",
                "keywords": _tokenize(raw_text)[:6],
                "descriptor": raw_text[:80],
                "value": {"raw": raw_text},
                "confidence": 0.5,
            }

        item = MemoryItem(
            kind=data.get("kind", "scratchpad"),
            keywords=data.get("keywords", _tokenize(raw_text)[:6]),
            descriptor=data.get("descriptor", raw_text[:80]),
            value=data.get("value", {"raw": raw_text}),
            source=source,
            run_id=run_id,
            goal_id=goal_id,
            confidence=float(data.get("confidence", 1.0)),
        )
        self._items.append(item)
        self._save()
        return item

    def record_outcome(
        self,
        *,
        tool_call: ToolCall,
        result_text: str,
        artifact_id: str | None,
        run_id: str,
        goal_id: str | None,
    ) -> MemoryItem:
        """No LLM — kind is tool_outcome by construction."""
        keywords = _tokenize(tool_call.name)
        for v in tool_call.arguments.values():
            keywords.extend(_tokenize(str(v)))
        keywords = list(dict.fromkeys(keywords))[:10]  # dedupe, cap at 10

        arg_preview = ", ".join(
            f"{k}={str(v)[:30]!r}" for k, v in list(tool_call.arguments.items())[:2]
        )
        descriptor = (
            f"{tool_call.name}({arg_preview}) → {result_text[:80]}"
        )
        value: dict = {
            "tool": tool_call.name,
            "arguments": tool_call.arguments,
            "result_preview": result_text[:500],
        }
        if artifact_id:
            value["artifact_id"] = artifact_id

        item = MemoryItem(
            kind="tool_outcome",
            keywords=keywords,
            descriptor=descriptor,
            value=value,
            artifact_id=artifact_id,
            source="action",
            run_id=run_id,
            goal_id=goal_id,
        )
        self._items.append(item)
        self._save()
        return item


# Module-level singleton
memory = MemoryService()
