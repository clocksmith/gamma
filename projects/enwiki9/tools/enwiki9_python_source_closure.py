#!/usr/bin/env python3
"""Resolve and hash the project-local Python import closure for an entry tool."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CONTRACT_ROOT = ROOT / "contracts" / "research" / "v1"
RESEARCH_CONTRACTS = TOOLS / "research_contracts.py"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module:
                modules.add(node.module)
                if node.module.endswith(".tools"):
                    modules.update(alias.name for alias in node.names)
    return modules


def resolve_local_module(module: str) -> Path | None:
    parts = module.split(".")
    candidates = (
        TOOLS.joinpath(*parts).with_suffix(".py"),
        TOOLS.joinpath(*parts, "__init__.py"),
        TOOLS / f"{parts[0]}.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def local_source_closure(entries: Iterable[Path]) -> list[Path]:
    pending = [path.resolve() for path in entries]
    closure: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        if path != TOOLS and TOOLS.resolve() not in path.parents:
            raise ValueError(f"Python closure entry escapes tools: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"Python closure entry is missing: {path}")
        closure.add(path)
        for module in imported_modules(path):
            dependency = resolve_local_module(module)
            if dependency is not None and dependency not in closure:
                pending.append(dependency)
    if RESEARCH_CONTRACTS.resolve() in closure:
        closure.update(path.resolve() for path in CONTRACT_ROOT.glob("*.json"))
    return sorted(closure, key=lambda path: path.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", nargs="+", type=Path)
    args = parser.parse_args()
    rows = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": f"sha256:{sha256(path)}",
        }
        for path in local_source_closure(args.entry)
    ]
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
