"""Known-answer lookup: find the same problem in the index, or abstain.

Candidates come from embedding similarity. Each candidate is rescored with a
fingerprint that keeps the details sibling problems differ in (House Robber I
vs II, Stock I-IV): the method signature, the numbers in the constraints, and
discriminating phrases such as "circle", "at most two transactions" or
"cooldown". A match is returned only when the best score clears a threshold
AND beats the runner-up by a margin; otherwise the lookup abstains. Both
thresholds are fitted on the dev queries and frozen before evaluation.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .records import DERIVED, LANE_ROOT
from .splits import IndexEntry

THRESHOLDS_PATH = LANE_ROOT / "contracts" / "lookup_thresholds.json"
EMBEDDINGS_PATH = DERIVED / "index_embeddings.npy"
EMBEDDING_KEYS_PATH = DERIVED / "index_embedding_keys.json"
TOP_K = 10

WEIGHTS = {"method": 0.10, "params": 0.05, "numbers": 0.10, "phrases": 0.10}

PHRASES = (
    "circle", "circular", "cooldown", "transaction fee", "at most two", "at most k", "at most one",
    "at most once", "as many transactions", "only once", "multiple times", "unlimited", "infinite number",
    "any order", "duplicates", "distinct", "unique", "sorted", "rotated", "negative", "non-negative",
    "binary search tree", "binary tree", "linked list", "directed", "undirected", "weighted", "cycle",
    "modulo 10^9 + 7", "modulo 109 + 7", "lexicographically smallest", "lexicographically largest",
    "subsequence", "subarray", "substring", "palindrome", "minimum", "maximum", "k times", "exactly k",
    "at least k", "two transactions", "k transactions", "adjacent", "consecutive", "contiguous",
    "in-place", "o(1) extra space", "o(log n)", "matrix", "grid", "tree", "graph", "string", "array",
)
_NUMBER_RE = re.compile(r"-?\d+(?:\s*\^\s*\d+)?")
_DEF_RE = re.compile(r"def\s+(\w+)\s*\(\s*self\s*(?:,\s*([^)]*))?\)")


@dataclass
class Fingerprint:
    method: str = ""
    params: tuple[str, ...] = ()
    numbers: frozenset[str] = frozenset()
    phrases: frozenset[str] = frozenset()


def _constraints_section(text: str) -> str:
    lowered = text.lower()
    at = lowered.rfind("constraints")
    return text[at:] if at >= 0 else text


def fingerprint(text: str) -> Fingerprint:
    method, params = "", ()
    match = _DEF_RE.search(text)
    if match:
        method = match.group(1)
        raw = match.group(2) or ""
        params = tuple(p.split(":")[0].split("=")[0].strip() for p in raw.split(",") if p.strip())
    numbers = frozenset(re.sub(r"\s+", "", n) for n in _NUMBER_RE.findall(_constraints_section(text)))
    lowered = " ".join(text.lower().split())
    phrases = frozenset(p for p in PHRASES if p in lowered)
    return Fingerprint(method, params, numbers, phrases)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def feature_bonus(query: Fingerprint, candidate: Fingerprint) -> dict[str, float]:
    return {
        "method": float(bool(query.method) and query.method == candidate.method),
        "params": float(bool(query.params) and query.params == candidate.params),
        "numbers": _jaccard(query.numbers, candidate.numbers),
        "phrases": _jaccard(query.phrases, candidate.phrases),
    }


@dataclass
class MatchResult:
    decision: str                      # match | abstain
    key: str | None
    score: float
    runner_up_key: str | None
    runner_up_score: float
    candidates: list[dict] = field(default_factory=list)
    seconds: float = 0.0


class LookupIndex:
    def __init__(self, entries: list[IndexEntry], embeddings: np.ndarray) -> None:
        if len(entries) != len(embeddings):
            raise ValueError("entries and embeddings differ in length")
        self.entries = entries
        self.embeddings = embeddings
        self.fingerprints = [fingerprint(e.query_text()) for e in entries]
        self.by_key = {e.key: i for i, e in enumerate(entries)}

    @classmethod
    def load(cls, entries: list[IndexEntry]) -> "LookupIndex":
        keys = json.loads(EMBEDDING_KEYS_PATH.read_text())
        embeddings = np.load(EMBEDDINGS_PATH)
        order = {k: i for i, k in enumerate(keys)}
        missing = [e.key for e in entries if e.key not in order]
        if missing:
            raise RuntimeError(f"{len(missing)} index entries have no embedding")
        return cls(entries, embeddings[[order[e.key] for e in entries]])

    def scored_candidates(self, query_text: str, query_vector: np.ndarray, top_k: int = TOP_K) -> list[dict]:
        sims = self.embeddings @ query_vector
        top = np.argsort(-sims)[:top_k]
        query_fp = fingerprint(query_text)
        out = []
        for i in top:
            bonus = feature_bonus(query_fp, self.fingerprints[i])
            score = float(sims[i]) + sum(WEIGHTS[k] * v for k, v in bonus.items())
            out.append({"key": self.entries[i].key, "cosine": float(sims[i]), "score": score, "features": bonus})
        out.sort(key=lambda c: -c["score"])
        return out

    def match(self, query_text: str, query_vector: np.ndarray, thresholds: dict[str, float]) -> MatchResult:
        candidates = self.scored_candidates(query_text, query_vector)
        return decide(candidates, thresholds)


def decide(candidates: list[dict], thresholds: dict[str, float]) -> MatchResult:
    best = candidates[0]
    second = candidates[1] if len(candidates) > 1 else {"key": None, "score": float("-inf")}
    accept = best["score"] >= thresholds["min_score"] and best["score"] - second["score"] >= thresholds["min_margin"]
    return MatchResult(
        decision="match" if accept else "abstain",
        key=best["key"] if accept else None,
        score=best["score"],
        runner_up_key=second["key"],
        runner_up_score=second["score"],
        candidates=candidates[:5],
    )


def fit_thresholds(dev_cases: list[tuple[list[dict], str | None]]) -> dict[str, float]:
    """Pick (min_score, min_margin) on dev: no wrong matches, then most correct.

    dev_cases: [(scored candidates, correct key or None for absent)].
    """
    scores = sorted({round(c[0][0]["score"], 4) for c in dev_cases})
    margins = sorted({0.0} | {round(c[0][0]["score"] - (c[0][1]["score"] if len(c[0]) > 1 else 0.0), 4) for c in dev_cases})
    best = None
    for min_score in [s - 1e-6 for s in scores] + [max(scores) + 1]:
        for min_margin in [m - 1e-6 for m in margins]:
            th = {"min_score": min_score, "min_margin": max(min_margin, 0.0)}
            correct = wrong = 0
            for candidates, truth in dev_cases:
                result = decide(candidates, th)
                if result.decision == "match":
                    if result.key == truth:
                        correct += 1
                    else:
                        wrong += 1
            key = (-wrong, correct, -th["min_score"], -th["min_margin"])
            if best is None or key > best[0]:
                best = (key, th, correct, wrong)
    _, th, correct, wrong = best
    return {**th, "dev_correct": correct, "dev_wrong": wrong, "dev_cases": len(dev_cases)}


def adapt_solution(code: str, entry: IndexEntry, query_method: str | None) -> str:
    """Rename the matched entry's method to the query's method name if they differ."""
    if not query_method or not entry.entry or entry.entry.get("method") == query_method:
        return code
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == entry.entry["method"]:
                    item.name = query_method
    return ast.unparse(tree)


def load_thresholds() -> dict[str, float]:
    return json.loads(Path(THRESHOLDS_PATH).read_text())
