"""Search macro-residual token additions with an isolated output receipt.

This is a Lane B helper for the XML scaffold macro candidates. It evaluates
candidate token additions against a parent program that exposes a module-level
S token list and reports archive-size deltas for the transformed LZMA stream.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import lzma
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
PROGRAMS_DIR = ROOT / "programs"
DATA_DEFAULT = ROOT / "data" / "enwik9"
PRESET = 9 | lzma.PRESET_EXTREME


DEFAULT_TOKENS = [
    "|",
    ".jpg",
    "\n===",
    "jpg",
    "Image:",
    "|name=",
    "Wikipedia:",
    "text-align:",
    "<br/>",
    "<ref ",
    "<ref>",
    "File:",
    "|url=",
    "&nbsp;",
    "</ref>",
    "<br />",
    "color:",
    "[[File:",
    'align="',
    'style="',
    "{{Coord",
    "{{coord",
    "|image=",
    "|caption=",
    "==",
    "height=",
    "png",
    "border=",
    "font-size:",
    "width=",
    "|title=",
    "Template:",
    "background:",
    "center|",
    "| ",
    "{{Main",
    ".png",
    "Category:",
    "class=",
    "\n==",
]


def load_parent_tokens(program_id: str) -> list[bytes]:
    path = PROGRAMS_DIR / program_id / "program.py"
    if not path.exists():
        raise SystemExit(f"missing parent program: {path}")
    spec = importlib.util.spec_from_file_location(f"macro_parent_{program_id}", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import parent program: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tokens = getattr(module, "S", None)
    if not isinstance(tokens, list) or not all(isinstance(token, bytes) for token in tokens):
        raise SystemExit(f"{program_id} does not expose a byte token list named S")
    return list(tokens)


def macro_encode(data: bytes, tokens: list[bytes]) -> bytes:
    ordered = sorted(enumerate(tokens, 1), key=lambda pair: -len(pair[1]))
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] == 0:
            out += b"\0\0"
            i += 1
            continue
        for code, token in ordered:
            if data.startswith(token, i):
                out += bytes((0, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def transformed_archive_size(data: bytes, tokens: list[bytes]) -> int:
    return len(b"T" + lzma.compress(macro_encode(data, tokens), preset=PRESET))


def source_cost_hint(token: bytes) -> int:
    return len(token) + 2


def row_for_token(
    *,
    data: bytes,
    tokens: list[bytes],
    base_size: int,
    token_text: str,
) -> dict[str, Any]:
    token = token_text.encode()
    archive_size = transformed_archive_size(data, tokens + [token])
    archive_delta = archive_size - base_size
    cost = source_cost_hint(token)
    return {
        "token": token_text,
        "token_len": len(token),
        "source_cost_hint": cost,
        "archive_size": archive_size,
        "archive_delta": archive_delta,
        "net_delta_hint": archive_delta + cost,
    }


def greedy_select(
    *,
    data: bytes,
    parent_tokens: list[bytes],
    candidate_strings: list[str],
    max_additions: int,
    min_net_gain: int,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    tokens = list(parent_tokens)
    parent_set = set(tokens)
    remaining = [
        token_text
        for token_text in dict.fromkeys(candidate_strings)
        if token_text.encode() not in parent_set
    ]
    current_size = transformed_archive_size(data, tokens)

    while remaining and len(selected) < max_additions:
        rows = [
            row_for_token(
                data=data,
                tokens=tokens,
                base_size=current_size,
                token_text=token_text,
            )
            for token_text in remaining
        ]
        rows.sort(key=lambda row: (row["net_delta_hint"], row["archive_delta"]))
        best = rows[0]
        if best["net_delta_hint"] > -min_net_gain:
            break
        selected.append(best)
        tokens.append(best["token"].encode())
        current_size = best["archive_size"]
        remaining = [token_text for token_text in remaining if token_text != best["token"]]

    return {
        "selected": selected,
        "final_archive_size": current_size,
        "selected_count": len(selected),
    }


def read_token_file(path: pathlib.Path) -> list[str]:
    tokens: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tokens.append(line)
    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", required=True, help="candidate id exposing S tokens")
    parser.add_argument("--data", type=pathlib.Path, default=DATA_DEFAULT)
    parser.add_argument("--limit", type=int, default=1_000_000)
    parser.add_argument("--token", action="append", default=[])
    parser.add_argument("--token-file", type=pathlib.Path)
    parser.add_argument("--greedy", action="store_true")
    parser.add_argument("--max-additions", type=int, default=8)
    parser.add_argument("--min-net-gain", type=int, default=1)
    args = parser.parse_args(argv)

    if args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.max_additions <= 0:
        raise SystemExit("--max-additions must be positive")
    if args.min_net_gain < 0:
        raise SystemExit("--min-net-gain must be non-negative")
    if not args.data.exists():
        raise SystemExit(f"missing data: {args.data}")

    lock_handle = None
    try:
        parent_tokens = load_parent_tokens(args.parent)
        candidate_strings = list(DEFAULT_TOKENS)
        candidate_strings.extend(args.token)
        if args.token_file is not None:
            candidate_strings.extend(read_token_file(args.token_file))

        data = args.data.read_bytes()[: args.limit]
        base_size = transformed_archive_size(data, parent_tokens)
        parent_set = set(parent_tokens)
        rows: list[dict[str, Any]] = []
        for token_text in dict.fromkeys(candidate_strings):
            token = token_text.encode()
            if token in parent_set:
                continue
            rows.append(
                row_for_token(
                    data=data,
                    tokens=parent_tokens,
                    base_size=base_size,
                    token_text=token_text,
                )
            )

        payload = {
            "parent": args.parent,
            "data_size": len(data),
            "base_archive_size": base_size,
            "rows": sorted(rows, key=lambda row: (row["net_delta_hint"], row["archive_delta"])),
        }
        if args.greedy:
            payload["greedy"] = greedy_select(
                data=data,
                parent_tokens=parent_tokens,
                candidate_strings=candidate_strings,
                max_additions=args.max_additions,
                min_net_gain=args.min_net_gain,
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    finally:
        pass


if __name__ == "__main__":
    sys.exit(main())
