"""
Lightweight semantic memory store.

Stores text entries with simple embeddings and provides similarity search.
"""

import json
import math
import re
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class MemoryEntry:
    """Single memory entry."""
    entry_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: List[float]


class SimpleEmbedder:
    """
    Deterministic bag-of-words embedder.

    Not a true semantic model, but stable and dependency-free.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        vec = [0.0] * self.dim
        for tok in tokens:
            idx = self._hash(tok) % self.dim
            vec[idx] += 1.0
        return self._normalize(vec)

    def _hash(self, token: str) -> int:
        h = 0
        for ch in token:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return h

    def _normalize(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


class SentenceTransformerEmbedder:
    """Semantic embedder using sentence-transformers (optional)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                f"sentence-transformers not available: {e}\n"
                "Install: pip install sentence-transformers"
            )
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> List[float]:
        vec = self.model.encode(text)
        if hasattr(vec, "tolist"):
            vec = vec.tolist()
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class MemoryStore:
    """Persisted memory store with similarity search."""

    def __init__(
        self,
        path: str,
        embedder: Optional[Any] = None,
        max_items: int = 2000,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or SimpleEmbedder()
        self.max_items = max_items
        self.entries: List[MemoryEntry] = []
        self._lock = threading.Lock()
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self._file_lock():
                for line in self.path.read_text().splitlines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    entry = MemoryEntry(
                        entry_id=data.get("entry_id", str(uuid.uuid4())),
                        text=data.get("text", ""),
                        metadata=data.get("metadata", {}),
                        embedding=data.get("embedding", []),
                    )
                    self.entries.append(entry)
        except Exception:
            self.entries = []

    def _persist_entry(self, entry: MemoryEntry) -> None:
        with self._file_lock():
            with self.path.open("a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        with self._lock:
            embedding = self.embedder.embed(text)
            entry = MemoryEntry(
                entry_id=str(uuid.uuid4()),
                text=text,
                metadata=metadata or {},
                embedding=embedding,
            )
            self.entries.append(entry)
            self._persist_entry(entry)

            if len(self.entries) > self.max_items:
                self.entries = self.entries[-self.max_items:]
                self._rewrite()

            return entry

    def _rewrite(self) -> None:
        with self._file_lock():
            with self.path.open("w") as f:
                for entry in self.entries:
                    f.write(json.dumps(asdict(entry)) + "\n")

    def search(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.25,
    ) -> List[Tuple[float, MemoryEntry]]:
        with self._lock:
            if not self.entries:
                return []

            q_vec = self.embedder.embed(query)
            scored = []
            for entry in self.entries:
                if not entry.embedding:
                    continue
                score = self._cosine(q_vec, entry.embedding)
                if score >= min_score:
                    scored.append((score, entry))

            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[:top_k]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot

    @contextmanager
    def _file_lock(self):
        lock_file = self._lock_path
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        f = lock_file.open("w")
        try:
            try:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except Exception:
                pass
            yield
        finally:
            try:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            f.close()
