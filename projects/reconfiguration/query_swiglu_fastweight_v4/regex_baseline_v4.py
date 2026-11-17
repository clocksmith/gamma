"""Frozen ~50-line lexical/BM25/regex support-lookup baseline for Track B1 v4."""
from __future__ import annotations

import math
import re

_LINE_RE = re.compile(r"^(.+?)\s*(?:=>|->|=|:)\s*(\S.*)$")
_WORD_RE = re.compile(r"[a-z0-9]{3,}")
_STOPWORDS = frozenset({
    "the", "and", "with", "from", "into", "over", "before", "after", "under",
    "item", "ticket", "case", "note", "log", "entry", "record", "signal", "query",
    "route", "each", "assigned", "sector", "code", "label", "class", "queue", "for",
})


def _content_tokens(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS}


def lookup_support_answer(support_text: str, query_line: str) -> dict[str, object]:
    """Retrieve best matching support RHS via IDF-weighted lexical overlap + prefix regex."""
    q_lhs = re.sub(r"\s*(?:=>|->|=|:)\s*$", "", query_line.strip())
    q_toks = _content_tokens(q_lhs)
    entries: list[tuple[str, set[str], str]] = []
    df: dict[str, int] = {}
    for raw_ln in support_text.splitlines():
        m = _LINE_RE.match(raw_ln.strip())
        if not m:
            continue
        lhs, rhs = m.group(1).strip(), m.group(2).strip()
        if not rhs:
            continue
        ltoks = _content_tokens(lhs)
        entries.append((lhs, ltoks, rhs))
        for tok in ltoks:
            df[tok] = df.get(tok, 0) + 1

    if not entries:
        return {"answer": "", "confidence": 0.0}

    # Exact substring / prefix match check first
    for lhs, _, rhs in entries:
        if lhs.lower() == q_lhs.lower():
            return {"answer": rhs, "confidence": 1.0}

    n_docs = float(len(entries))
    q_norm = sum(math.log(1.0 + n_docs / float(df.get(t, 1))) for t in q_toks) or 1.0
    best_rhs = entries[0][2]
    best_score = -1.0
    for _, ltoks, rhs in entries:
        inter = q_toks & ltoks
        score = sum(math.log(1.0 + n_docs / float(df.get(t, 1))) for t in inter) / q_norm
        if score > best_score:
            best_score = score
            best_rhs = rhs

    return {"answer": best_rhs, "confidence": float(max(0.0, min(1.0, best_score)))}
