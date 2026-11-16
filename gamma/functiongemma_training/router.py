"""
Expert router for per-group LoRA selection.
"""

from typing import Dict, List


class ExpertRouter:
    """Route queries to expert groups based on keywords."""

    KEYWORD_ROUTES: Dict[str, List[str]] = {
        "search": ["find", "search", "grep", "where", "usage", "definition"],
        "read": ["read", "show", "contents", "file", "list"],
        "write": ["write", "edit", "change", "update", "fix", "patch"],
        "test": ["test", "run", "check", "verify", "pass", "fail"],
    }

    def route(self, query: str) -> str:
        query_lower = query.lower()
        scores: Dict[str, int] = {}
        for group, keywords in self.KEYWORD_ROUTES.items():
            scores[group] = sum(1 for kw in keywords if kw in query_lower)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "search"
