from __future__ import annotations

import subprocess


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

XZ_ARGS = [
    "xz",
    "-q",
    "-c",
    "-T1",
    "--check=crc32",
    "--lzma2=preset=9e,dict=1024MiB",
]


def _encode(data: bytes) -> bytes:
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


def _decode(data: bytes) -> bytes:
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
    encoded = _encode(data)
    return subprocess.run(
        XZ_ARGS,
        input=encoded,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def decompress(data: bytes) -> bytes:
    encoded = subprocess.run(
        ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"],
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    return _decode(encoded)
