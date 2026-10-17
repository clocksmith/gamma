"""Normalized problem record shared by importers, routes and the evaluator."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

LANE_ROOT = Path(__file__).resolve().parents[1]
DATA = LANE_ROOT / "data"
RAW = DATA / "raw"
DERIVED = DATA / "derived"

# Evidence ceilings a problem's tests can support.
EXAMPLE = "example_passed"
INDEPENDENT = "independent_tests_passed"


@dataclass
class Problem:
    uid: str                      # "<source>:<id>", unique across sources
    source: str                   # lcd | lcb | cf | doocs
    source_id: str
    title: str
    slug: str                     # LeetCode slug when the problem is from LeetCode, else ""
    statement: str
    io_mode: str                  # functional | stdin
    starter_code: str = ""
    entry: dict[str, str] = field(default_factory=dict)
    params: list[list[str]] = field(default_factory=list)   # [[name, annotation]]
    date: str = ""
    difficulty: str = ""
    tags: list[str] = field(default_factory=list)
    license: str = ""
    attribution: str = ""
    evidence_ceiling: str = EXAMPLE
    cpu_seconds: float = 2.0
    memory_bytes: int = 512 * 1024 * 1024
    checker: str | None = None
    reference_solutions: list[str] = field(default_factory=list)
    public_tests: list[dict[str, Any]] = field(default_factory=list)
    hidden_tests_path: str = ""   # relative to DERIVED; tests kept out of the index file
    import_notes: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Problem":
        return cls(**data)

    def query_text(self) -> str:
        """What a user would paste: statement plus starter code when present."""
        if self.starter_code.strip():
            return f"{self.statement.strip()}\n\n{self.starter_code.rstrip()}\n"
        return self.statement.strip() + "\n"


def safe_name(uid: str) -> str:
    return uid.replace(":", "__").replace("/", "_")


def write_problems(path: Path, problems: Iterable[Problem]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for problem in problems:
            handle.write(problem.to_json() + "\n")
            count += 1
    return count


def read_problems(path: Path) -> Iterator[Problem]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield Problem.from_dict(json.loads(line))


def write_hidden_tests(problem: Problem, tests: list[dict[str, Any]]) -> None:
    relative = Path("tests") / f"{safe_name(problem.uid)}.json"
    target = DERIVED / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(tests), encoding="utf-8")
    problem.hidden_tests_path = str(relative)


def load_hidden_tests(problem: Problem) -> list[dict[str, Any]]:
    if not problem.hidden_tests_path:
        return []
    from .test_corrections import apply
    return apply(problem, json.loads((DERIVED / problem.hidden_tests_path).read_text(encoding="utf-8")))
