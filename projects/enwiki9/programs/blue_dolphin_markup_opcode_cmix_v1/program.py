"""blue_dolphin_markup_opcode_cmix_v1 — Phase 2 same-backend ablation.

Reuses ast_opcode_lzma_v1's 38-token markup substitution, but pipes the
transformed stream through embedded cmix instead of xz. Tests whether the
opcode layer's xz win at 100 MB generalizes to a context mixer.

Decision rule:
  - If S < cmix_wrapped on the same scope: opcode layer composes with cmix;
    keep, but consider migrating the information into sidecar state.
  - If S >= cmix_wrapped: opcode layer was xz-specific; retire on cmix
    substrate.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ESC = 0
LIT_ESC = 255

TOKENS = [
    b'<text xml:space="preserve">',
    b"</text>", b"<page>", b"</page>",
    b"<revision>", b"</revision>",
    b"<contributor>", b"</contributor>",
    b"<timestamp>", b"</timestamp>",
    b"<username>", b"</username>",
    b"<comment>", b"</comment>",
    b"<title>", b"</title>",
    b"<id>", b"</id>",
    b"<minor />",
    b"{{", b"}}",
    b"[[Category:", b"[[Image:", b"[[", b"]]",
    b"&quot;", b"&lt;", b"&gt;", b"&amp;",
    b"http://", b"https://",
    b"<ref", b"</ref>",
    b"|thumb", b"|right", b"|left",
    b"Category:", b"File:", b"Image:",
]

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
DECODE_TABLE = {i: token for i, token in enumerate(TOKENS, 1)}


def _load_cmix():
    p = pathlib.Path(__file__).resolve().parent.parent / "cmix_wrapped" / "program.py"
    spec = importlib.util.spec_from_file_location("_cmix_wrapped_for_blue_dolphin", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_CMIX = _load_cmix()


def _encode_opcode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] == ESC:
            out.extend((ESC, LIT_ESC))
            i += 1
            continue
        for code, token in TOKENS_BY_LEN:
            if data.startswith(token, i):
                out.extend((ESC, code))
                i += len(token)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _decode_opcode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != ESC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("truncated opcode escape")
        code = data[i + 1]
        if code == LIT_ESC:
            out.append(ESC)
        else:
            out.extend(DECODE_TABLE[code])
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    return _CMIX.compress(_encode_opcode(data))


def decompress(data: bytes) -> bytes:
    return _decode_opcode(_CMIX.decompress(data))
