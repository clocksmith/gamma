#!/usr/bin/env python3
"""Create a Lane B macro-residual LZMA candidate from a parent token table."""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import textwrap
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"


def load_parent_tokens(program_id: str) -> list[bytes]:
    path = PROGRAMS / program_id / "program.py"
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


def read_token_file(path: pathlib.Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def token_blob(tokens: list[bytes]) -> str:
    delimiter = b"\x01"
    if any(delimiter in token for token in tokens):
        raise SystemExit("token contains reserved delimiter byte 0x01")
    return repr(delimiter.join(tokens))


def program_source(tokens: list[bytes]) -> str:
    blob = token_blob(tokens)
    return textwrap.dedent(
        f"""
        import lzma
        P=9|lzma.PRESET_EXTREME
        S={blob}.split(b'\\1')
        A=sorted(enumerate(S,1),key=lambda p:-len(p[1]));D=dict(enumerate(S,1))
        def _e(x):
         o=bytearray();i=0;n=len(x)
         while i<n:
          if x[i]==0:o+=b'\\0\\0';i+=1;continue
          for c,t in A:
           if x.startswith(t,i):o+=bytes((0,c));i+=len(t);break
          else:o.append(x[i]);i+=1
         return bytes(o)
        def _d(x):
         o=bytearray();i=0;n=len(x)
         while i<n:
          b=x[i]
          if b:o.append(b);i+=1;continue
          if i+1>=n:raise ValueError('truncated')
          c=x[i+1];o+=D[c] if c else b'\\0';i+=2
         return bytes(o)
        def compress(x):
         r=b'R'+lzma.compress(x,preset=P);t=b'T'+lzma.compress(_e(x),preset=P)
         return t if len(t)<len(r) else r
        def decompress(x):
         p=lzma.decompress(x[1:])
         if x[:1]==b'R':return p
         if x[:1]==b'T':return _d(p)
         raise ValueError('mode')
        """
    ).strip() + "\n"


def load_parent_meta(parent_id: str) -> dict[str, Any]:
    path = PROGRAMS / parent_id / "meta.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--token", action="append", default=[])
    parser.add_argument("--token-file", type=pathlib.Path)
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--status", default="candidate")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--description",
        default="Macro-residual XML scaffold token table generated from measured additions.",
    )
    parser.add_argument(
        "--hypothesis",
        default=(
            "Measured token additions can reduce the transformed LZMA archive "
            "more than their counted source bytes."
        ),
    )
    args = parser.parse_args()

    additions = list(args.token)
    if args.token_file:
        additions.extend(read_token_file(args.token_file))
    if not additions:
        raise SystemExit("provide at least one --token or --token-file entry")

    tokens = load_parent_tokens(args.parent)
    seen = set(tokens)
    added: list[str] = []
    for text in additions:
        token = text.encode()
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        added.append(text)
    if not added:
        raise SystemExit("all requested tokens already exist in parent")
    if len(tokens) > 255:
        raise SystemExit("macro table exceeds one-byte opcode capacity")

    source = program_source(tokens)
    out_dir = PROGRAMS / args.id

    parent_meta = load_parent_meta(args.parent)
    meta = {
        "id": args.id,
        "aliases": args.alias,
        "family": "lane_b_macro_residual",
        "mechanism": "macro_residual",
        "backend": "lzma_extreme",
        "status": args.status,
        "parent": args.parent,
        "description": args.description,
        "hypothesis": args.hypothesis,
        "deps": [],
        "macro_parent_status": parent_meta.get("status"),
        "added_tokens": added,
        "measured": {},
        "verdict": "Unmeasured generated macro-residual candidate.",
        "pgsg": {
            "nodes": [
                {
                    "id": "macro_table",
                    "type": "parser",
                    "payload": {
                        "discrete": {
                            "mode": "static_xml_wiki_macro_tokens",
                            "added_tokens": added,
                        }
                    },
                },
                {
                    "id": "escape_stream",
                    "type": "transform",
                    "payload": {"discrete": {"mode": "zero_escape_macro_residual"}},
                },
                {
                    "id": "backend",
                    "type": "codec",
                    "payload": {"discrete": {"codec": "lzma_extreme_with_raw_fallback"}},
                },
            ],
            "edges": [
                {"from": "macro_table", "to": "escape_stream", "stream": "token_table"},
                {"from": "escape_stream", "to": "backend", "stream": "payload"},
            ],
        },
    }
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "program.py").write_text(source)
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "id": args.id,
                "dir": str(out_dir),
                "dry_run": args.dry_run,
                "parent": args.parent,
                "added_tokens": added,
                "token_count": len(tokens),
                "program_size": len(source.encode()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
