from __future__ import annotations

import bz2

E = 0
L = 255
T = b"""<text xml:space="preserve">
</text>
<page>
</page>
<revision>
</revision>
<contributor>
</contributor>
<timestamp>
</timestamp>
<username>
</username>
<comment>
</comment>
<title>
</title>
<id>
</id>
<minor />
{{
}}
[[Category:
[[Image:
[[
]]
&quot;
&lt;
&gt;
&amp;
http://
https://
<ref
</ref>
|thumb
|right
|left
Category:
File:
Image:""".splitlines()
S = sorted(enumerate(T, 1), key=lambda x: -len(x[1]))
D = dict(enumerate(T, 1))


def _enc(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == E:
            out.extend((E, L))
            i += 1
            continue
        for c, t in S:
            if data.startswith(t, i):
                out.extend((E, c))
                i += len(t)
                break
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def _dec(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i]:
            out.append(data[i])
            i += 1
            continue
        c = data[i + 1]
        out.extend(b"\0" if c == L else D[c])
        i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    return bz2.compress(_enc(data), compresslevel=9)


def decompress(data: bytes) -> bytes:
    return _dec(bz2.decompress(data))
