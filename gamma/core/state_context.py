"""Lossless, query-directed slicing of explicit state-transition logs.

This is a symbolic context preprocessor, not a learned weight transformation.
It keeps original source lines and their transitive dependencies. Unknown text,
operations, queries or inconsistent examples return the original prompt intact.

Supported lines: SET/UPDATE name = literal, COPY name = source,
ADD name += integer, and READ name => STATE=literal demonstrations. A single
``State transition log:`` header and blank lines are also accepted. Literals
are signed integers or identifiers. The final query is ``READ name =>``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys


_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_VALUE = rf"(?:{_NAME}|[+-]?\d+)"
_ASSIGN = re.compile(rf"(SET|UPDATE) ({_NAME}) = ({_VALUE})")
_COPY = re.compile(rf"COPY ({_NAME}) = ({_NAME})")
_ADD = re.compile(rf"ADD ({_NAME}) \+= ([+-]?\d+)")
_EXAMPLE = re.compile(rf"READ ({_NAME}) => STATE=({_VALUE})")
_QUERY = re.compile(rf"READ ({_NAME}) =>")


class UnsupportedStateContext(ValueError):
    """The log cannot be safely interpreted by this closed grammar."""


@dataclass(frozen=True)
class _Event:
    line: int
    name: str
    value: str
    dependencies: tuple[int, ...]


def _prompt(context: str, query: str) -> str:
    separator = "" if not context or context.endswith(("\n", "\r")) else "\n"
    return context + separator + query


def _parse(context: str):
    events: list[_Event] = []
    latest: dict[str, int] = {}
    initializers: dict[str, int] = {}
    roots: set[int] = set()
    retained: set[int] = set()
    lines = context.splitlines(keepends=True)
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or (line == "State transition log:" and line_number == 1):
            retained.add(line_number)
            continue
        match = _ASSIGN.fullmatch(line)
        creates_definition = False
        if match:
            operation, name, value = match.groups()
            if operation == "UPDATE" and name not in latest:
                raise UnsupportedStateContext(f"line {line_number}: UPDATE of undefined {name}")
            dependencies = (initializers[name],) if operation == "UPDATE" else ()
            creates_definition = operation == "SET"
        elif (match := _COPY.fullmatch(line)):
            name, source = match.groups()
            if source not in latest:
                raise UnsupportedStateContext(f"line {line_number}: COPY of undefined {source}")
            dependencies = (latest[source],)
            value = events[latest[source]].value
            creates_definition = True
        elif (match := _ADD.fullmatch(line)):
            name, delta = match.groups()
            if name not in latest or not re.fullmatch(r"[+-]?\d+", events[latest[name]].value):
                raise UnsupportedStateContext(f"line {line_number}: ADD needs initialized integer {name}")
            dependencies = (latest[name],)
            try:
                value = str(int(events[latest[name]].value) + int(delta))
            except ValueError as error:
                raise UnsupportedStateContext(f"line {line_number}: unsupported integer size") from error
        elif (match := _EXAMPLE.fullmatch(line)):
            name, expected = match.groups()
            if name not in latest or events[latest[name]].value != expected:
                raise UnsupportedStateContext(f"line {line_number}: inconsistent READ example for {name}")
            roots.add(latest[name])
            retained.add(line_number)
            continue
        else:
            raise UnsupportedStateContext(f"line {line_number}: unsupported syntax")
        event_id = len(events)
        events.append(_Event(line_number, name, value, dependencies))
        latest[name] = event_id
        # UPDATE needs a prior definition, not every overwritten value. COPY
        # defines its target too; retain that operation and its source closure.
        if creates_definition:
            initializers[name] = event_id
    return lines, events, latest, roots, retained


def read_state(context: str, query: str) -> str:
    """Replay the full supported log and return the requested value, or raise."""
    match = _QUERY.fullmatch(query.strip())
    if not match:
        raise UnsupportedStateContext("unsupported query; expected READ name =>")
    _, events, latest, _, _ = _parse(context)
    name = match.group(1)
    if name not in latest:
        raise UnsupportedStateContext(f"query reads undefined {name}")
    return events[latest[name]].value


def compact_state_context(context: str, query: str) -> dict:
    """Return a source-linked slice; unsupported input falls back without loss.

    Only context and query enter this API: no evaluation answer, tokenizer,
    model or task ID is available to the compiler. Source references use
    one-based line numbers and SHA-256 of each original line including newline.
    """
    if not isinstance(context, str) or not isinstance(query, str):
        raise TypeError("context and query must be strings")
    result = {
        "schema": "gamma.state-context/v1",
        "classification": "symbolic query-aware context preprocessing; no weight updates",
        "source_sha256": hashlib.sha256(context.encode()).hexdigest(),
        "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
        "supported": False,
        "reason": None,
        "context_text": context,
        "prompt": _prompt(context, query),
        "source_line_count": len(context.splitlines()),
        "retained_line_count": len(context.splitlines()),
        "source_refs": [],
    }
    try:
        match = _QUERY.fullmatch(query.strip())
        if not match:
            raise UnsupportedStateContext("unsupported query; expected READ name =>")
        lines, events, latest, roots, retained = _parse(context)
        name = match.group(1)
        if name not in latest:
            raise UnsupportedStateContext(f"query reads undefined {name}")
        roots.add(latest[name])
        pending = list(roots)
        visited = set()
        while pending:
            event_id = pending.pop()
            if event_id in visited:
                continue
            visited.add(event_id)
            event = events[event_id]
            retained.add(event.line)
            pending.extend(event.dependencies)
        compacted = "".join(raw for i, raw in enumerate(lines, 1) if i in retained)
        # An executable consistency check also catches implementation mistakes
        # in dependency closure before an unsafe compacted prompt can escape.
        if read_state(compacted, query) != events[latest[name]].value:
            raise RuntimeError("state slice changed the requested value")
        result.update(
            supported=True,
            context_text=compacted,
            prompt=_prompt(compacted, query),
            retained_line_count=len(retained),
            source_refs=[
                {"line": i, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
                for i, raw in enumerate(lines, 1) if i in retained
            ],
        )
    except UnsupportedStateContext as error:
        result["reason"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", help="UTF-8 event-log file, or - for stdin")
    parser.add_argument("--query", required=True, help="e.g. READ REG_03 =>")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prompt-only", action="store_true")
    mode.add_argument("--read-state", action="store_true", help="Replay the supported log and return its exact STATE=value without a model")
    args = parser.parse_args()
    context = sys.stdin.read() if args.context == "-" else Path(args.context).read_text()
    result = compact_state_context(context, args.query)
    if args.read_state:
        if not result["supported"]:
            parser.error(f"Cannot answer unsupported input: {result['reason']}")
        result["answer"] = f"STATE={read_state(context, args.query)}"
    print(result["prompt"] if args.prompt_only else json.dumps(result, indent=2))
    if not result["supported"]:
        print(f"Unchanged fallback: {result['reason']}", file=sys.stderr)


if __name__ == "__main__":
    main()
