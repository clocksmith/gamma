import lzma

A = b"""<text xml:space="preserve">
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
Image:
==External links==
==References==
==See also==
== External links ==
== References ==
== See also ==
==History==
== History ==
==Further reading==
{{cite book
{{cite web
{{cite web\x20
{{cite journal
{{citation
{{main
{{ref
{{note
{{IPA
{{Commons
{{commons
{{disambig
{{succession box
{{start box
{{end box
{{flagicon
{{otheruses
{{DEFAULTSORT:
{{Infobox
| align=
|align=
| title=
|title=
| Title =
| style=
|style=
| author=
| author =
| authorlink =
| accessdate=
| accessyear=
| publisher=
| publisher =
| year=
| year =
| url=
| pages=
| volume=
| issue=
| journal=
| location =
| first =
| last =
| before=
| after=
|- style=
|- bgcolor=
|colspan=""".splitlines()
C = b"""[[File:
[[image:
[[Special:
[[Wikipedia:
[[:Category:
[[User talk:
<ip>
</ip>
<br />
<br>
ISBN\x20
ISSN\x20
www.""".splitlines()
L = b"de fr pl nl es sv ja pt it fi zh he ru da eo no cs ca ko hu bg uk gl sl sk lt sr id et ar tr hr nn ro th io is vi el la bs ms eu af tl mk fa simple".split()
T = A + [b"[[%s:" % x for x in L] + C
S = sorted(enumerate(T, 1), key=lambda x: -len(x[1]))
D = dict(enumerate(T, 1))
B = {}
for c, t in S:
    B.setdefault(t[0], []).append((c, t))
F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 30}]


def E(d):
    o = bytearray()
    i = 0
    n = len(d)
    while i < n:
        b = d[i]
        if b == 0:
            o += b"\0\xff"
            i += 1
            continue
        for c, t in B.get(b, ()):
            if d.startswith(t, i):
                o += bytes((0, c))
                i += len(t)
                break
        else:
            o.append(b)
            i += 1
    return bytes(o)


def R(d):
    o = bytearray()
    i = 0
    n = len(d)
    while i < n:
        b = d[i]
        if b:
            o.append(b)
            i += 1
            continue
        c = d[i + 1]
        o += b"\0" if c == 255 else D[c]
        i += 2
    return bytes(o)


def compress(d):
    return lzma.compress(E(d), format=lzma.FORMAT_XZ, filters=F)


def decompress(d):
    return R(lzma.decompress(d))
