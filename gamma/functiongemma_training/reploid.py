"""
Reploid TraceStore converter.

Converts TraceStore JSONL entries into FunctionGemma training experiences.
"""

import json
from typing import Any, Dict, List, Optional


_QUERY_EVENT_TYPES = {
    "agent:task",
    "llm:request",
    "llm:prompt",
    "user:message",
    "query",
    "task",
}

_QUERY_FIELDS = ("query", "prompt", "content", "task", "goal", "input")


def parse_reploid_traces(jsonl_path: str) -> List[Dict[str, Any]]:
    """
    Parse Reploid TraceStore JSONL to experiences.

    TraceStore format:
      {"type": "tool:execute", "payload": {"tool": "grep", "args": {...}, ...}}

    Output:
      [{"query": "...", "tool": "grep", "args": {...}}, ...]
    """
    experiences: List[Dict[str, Any]] = []
    last_query: Optional[str] = None

    with open(jsonl_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            payload = entry.get("payload", {}) or {}

            if entry_type in _QUERY_EVENT_TYPES:
                last_query = _extract_query(payload) or last_query
                continue

            if entry_type == "tool:execute":
                tool = payload.get("tool") or payload.get("name")
                args = payload.get("args") or {}
                if not tool:
                    continue
                experiences.append({
                    "query": last_query or "",
                    "tool": tool,
                    "args": args,
                })

    return experiences


def _extract_query(payload: Dict[str, Any]) -> Optional[str]:
    for key in _QUERY_FIELDS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
