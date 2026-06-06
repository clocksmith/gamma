"""purple_parrot_markup_opcode_cmix — markup-token opcode substitution
preprocessor on top of cmix as the back-end.

Layer 1: identical 38-token MediaWiki/XML opcode substitution to
`ast_opcode_lzma_v1` (0x00 + code_byte for tokens; 0x00 + 0xff escape for
literal 0x00 bytes; longest-token-first matching).

Layer 2: cmix as the back-end via subprocess to system cmix on PATH.

Architecture test (step 2 of the locked next-steps): the opcode layer beat
xz_lzma2_1g on a 100 MB prefix by 100,727 bytes (-0.41%). The open question
is whether the same substitution helps a context mixer (cmix) or fights its
existing preprocessor's preemption. This program's S vs. cmix_wrapped's S on
the same scope answers that.

Score-honesty caveat: the cmix binary is NOT inlined here (per the
schema_cmix / title_table_cmix convention — relies on PATH). For a
leaderboard-eligible row, inline as in cmix_wrapped/program.py.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

ESC = 0
LIT_ESC = 255

TOKENS = [
    b'<text xml:space="preserve">',
    b"</text>",
    b"<page>",
    b"</page>",
    b"<revision>",
    b"</revision>",
    b"<contributor>",
    b"</contributor>",
    b"<timestamp>",
    b"</timestamp>",
    b"<username>",
    b"</username>",
    b"<comment>",
    b"</comment>",
    b"<title>",
    b"</title>",
    b"<id>",
    b"</id>",
    b"<minor />",
    b"{{",
    b"}}",
    b"[[Category:",
    b"[[Image:",
    b"[[",
    b"]]",
    b"&quot;",
    b"&lt;",
    b"&gt;",
    b"&amp;",
    b"http://",
    b"https://",
    b"<ref",
    b"</ref>",
    b"|thumb",
    b"|right",
    b"|left",
    b"Category:",
    b"File:",
    b"Image:",
]

TOKENS_BY_LEN = sorted(enumerate(TOKENS, 1), key=lambda x: len(x[1]), reverse=True)
DECODE = {i: token for i, token in enumerate(TOKENS, 1)}

_CMIX = shutil.which("cmix")


def _require_cmix() -> str:
    if _CMIX is None:
        raise RuntimeError(
            "cmix not on PATH; install from https://github.com/byronknoll/cmix"
        )
    return _CMIX


def _cmix(flag: str, data: bytes) -> bytes:
    binary = _require_cmix()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in")
        dst = os.path.join(td, "out")
        with open(src, "wb") as f:
            f.write(data)
        subprocess.run(
            [binary, flag, src, dst],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(dst, "rb") as f:
            return f.read()


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
            out.extend(DECODE[code])
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    return _cmix("-c", _encode_opcode(data))


def decompress(data: bytes) -> bytes:
    return _decode_opcode(_cmix("-d", data))
