#!/usr/bin/env python3
"""Validate recursive component charters and render their repository index."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "COMPONENT_INDEX.md"
MAX_WORDS = 250
REQUIRED_SECTIONS = (
    "Target",
    "Authority",
    "Scope",
    "Contracts",
    "Invariants",
    "Acceptance",
    "Non-goals",
    "Freedom",
)
SKIP_DIRECTORIES = {
    "__pycache__",
    "data",
    "dist",
    "mind_meld_results",
    "models",
    "node_modules",
    "output",
    "reports",
    "results",
    "run_logs",
    "sessions",
}
HEADING_RE = re.compile(r"^# CATSCAN: (?P<name>[^\n]+)$", re.MULTILINE)
PARENT_RE = re.compile(r"^Parent: (?P<value>[^\n]+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class Charter:
    path: Path
    name: str
    identifier: str
    parent_value: str
    target: str
    text: str
    sections: dict[str, str]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def find_charter_paths() -> list[Path]:
    paths: list[Path] = []
    for directory, names, files in os.walk(ROOT):
        names[:] = sorted(
            name
            for name in names
            if not name.startswith(".") and name not in SKIP_DIRECTORIES
        )
        if "CATSCAN.md" in files:
            paths.append(Path(directory) / "CATSCAN.md")
    return sorted(paths, key=lambda path: (len(path.relative_to(ROOT).parts), relative(path)))


def component_identifier(name: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", name.casefold()))


def section_text(text: str, name: str) -> str | None:
    marker = f"## {name}\n"
    start = text.find(marker)
    if start < 0:
        return None
    body_start = start + len(marker)
    next_section = text.find("\n## ", body_start)
    return text[body_start:] if next_section < 0 else text[body_start:next_section]


def parse_charter(path: Path) -> tuple[Charter | None, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    heading = HEADING_RE.search(text)
    parent = PARENT_RE.search(text)
    if heading is None:
        errors.append(f"{relative(path)}: missing '# CATSCAN: <Component>' heading")
    if parent is None:
        errors.append(f"{relative(path)}: missing Parent field")
    sections: dict[str, str] = {}
    for name in REQUIRED_SECTIONS:
        body = section_text(text, name)
        if body is None or not body.strip():
            errors.append(f"{relative(path)}: missing or empty '{name}' section")
        else:
            sections[name] = body.strip()

    words = len(WORD_RE.findall(text))
    if words > MAX_WORDS:
        errors.append(
            f"{relative(path)}: {words} words exceeds the {MAX_WORDS}-word charter limit"
        )
    contracts = sections.get("Contracts", "")
    if not re.search(r"^- Input:", contracts, re.MULTILINE):
        errors.append(f"{relative(path)}: Contracts must declare an Input")
    if not re.search(r"^- Output:", contracts, re.MULTILINE):
        errors.append(f"{relative(path)}: Contracts must declare an Output")

    target_text = " ".join(sections.get("Target", "").split())
    if target_text.startswith(("- ", "* ")) or "\n" in sections.get("Target", "").strip():
        errors.append(f"{relative(path)}: Target must be one concise paragraph")

    if errors or heading is None or parent is None:
        return None, errors
    name = heading.group("name").strip()
    identifier = component_identifier(name)
    if not identifier:
        errors.append(f"{relative(path)}: component name has no stable identifier")
        return None, errors
    return (
        Charter(
            path=path,
            name=name,
            identifier=identifier,
            parent_value=parent.group("value").strip(),
            target=target_text,
            text=text,
            sections=sections,
        ),
        errors,
    )


def local_link_path(charter: Charter, raw_link: str) -> Path | None:
    link = raw_link.strip().strip("<>")
    if link.startswith(("http://", "https://", "mailto:", "#")):
        return None
    path_text = unquote(link.split("#", 1)[0])
    if not path_text:
        return None
    return (charter.path.parent / path_text).resolve()


def nearest_parent_charter(path: Path, charter_paths: set[Path]) -> Path | None:
    directory = path.parent.parent
    while True:
        candidate = directory / "CATSCAN.md"
        if candidate in charter_paths:
            return candidate
        if directory == ROOT:
            return None
        if ROOT not in directory.parents:
            return None
        directory = directory.parent


def validate_charters(charters: list[Charter]) -> list[str]:
    errors: list[str] = []
    by_path = {charter.path.resolve(): charter for charter in charters}
    identifiers: dict[str, Path] = {}
    for charter in charters:
        previous = identifiers.get(charter.identifier)
        if previous is not None:
            errors.append(
                f"{relative(charter.path)}: duplicate component identifier "
                f"{charter.identifier!r} also used by {relative(previous)}"
            )
        identifiers[charter.identifier] = charter.path

        expected_parent = nearest_parent_charter(charter.path, set(by_path))
        if charter.path == ROOT / "CATSCAN.md":
            if charter.parent_value.casefold() != "none":
                errors.append("CATSCAN.md: repository root Parent must be 'none'")
        else:
            links = LINK_RE.findall(charter.parent_value)
            if len(links) != 1:
                errors.append(
                    f"{relative(charter.path)}: Parent must contain exactly one local link"
                )
            else:
                declared_parent = local_link_path(charter, links[0])
                if declared_parent != expected_parent:
                    expected = relative(expected_parent) if expected_parent else "none"
                    actual = (
                        relative(declared_parent)
                        if declared_parent is not None and ROOT in declared_parent.parents
                        else str(declared_parent)
                    )
                    errors.append(
                        f"{relative(charter.path)}: Parent resolves to {actual}; expected {expected}"
                    )

        for raw_link in LINK_RE.findall(charter.text):
            linked_path = local_link_path(charter, raw_link)
            if linked_path is None:
                continue
            if linked_path != ROOT and ROOT not in linked_path.parents:
                errors.append(
                    f"{relative(charter.path)}: link escapes repository: {raw_link}"
                )
            elif not linked_path.exists():
                errors.append(
                    f"{relative(charter.path)}: missing linked path: {raw_link}"
                )

        acceptance_links = LINK_RE.findall(charter.sections.get("Acceptance", ""))
        if not acceptance_links:
            errors.append(
                f"{relative(charter.path)}: Acceptance must link test, report, or registry evidence"
            )
    return errors


def render_index(charters: list[Charter]) -> str:
    by_path = {charter.path.resolve(): charter for charter in charters}
    lines = [
        "# Gamma component index",
        "",
        "Generated by `python3 tools/catscan.py --write`; do not edit by hand.",
        "",
        "Agents read the linked charters from the repository root down to the file they change.",
        "",
        "| Component | Charter | Parent | Target |",
        "| --- | --- | --- | --- |",
    ]
    for charter in charters:
        parent_path = nearest_parent_charter(charter.path, set(by_path))
        parent_name = by_path[parent_path.resolve()].name if parent_path else "none"
        charter_link = Path("..") / charter.path.relative_to(ROOT)
        target = charter.target.replace("|", "\\|")
        lines.append(
            f"| `{charter.name}` | [{relative(charter.path)}]({charter_link.as_posix()}) "
            f"| `{parent_name}` | {target} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="refresh the component index")
    mode.add_argument("--check", action="store_true", help="check charters and index")
    args = parser.parse_args()

    parse_errors: list[str] = []
    charters: list[Charter] = []
    for path in find_charter_paths():
        charter, errors = parse_charter(path)
        parse_errors.extend(errors)
        if charter is not None:
            charters.append(charter)
    errors = parse_errors + validate_charters(charters)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    rendered = render_index(charters)
    if args.write:
        INDEX_PATH.write_text(rendered, encoding="utf-8")
        print(f"wrote {relative(INDEX_PATH)} ({len(charters)} components)")
        return 0
    current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else None
    if current != rendered:
        print(
            "component index is missing or stale; run python3 tools/catscan.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"CATSCAN valid ({len(charters)} components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
