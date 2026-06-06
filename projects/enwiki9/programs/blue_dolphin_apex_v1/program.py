"""blue_dolphin_apex_v1 — best-damn shippable.

Architecture: markup opcode preprocessing + cmix substrate. Two stages,
nothing else, code-golfed.

Layer 1: 38-token MediaWiki/XML markup substitution (escape 0x00).
  - Same token set as yellow_tucan_markup_opcode_lzma2_1g_v1, which beat
    bare xz at 100 MB by 100,727 bytes. The substitution layer is the
    only Track 2 idea with a measured full-prefix win.

Layer 2: cmix v21 substrate (loaded from sibling cmix_wrapped/program.py).
  - cmix is the only known coder that gets enwik9 below 1.0 b/B without
    shipping multi-hundred-MB neural weights.

Honest gate to 10%:
  - This program lands ~110-113 MB on full corpus (11%), not 100 MB (10%).
  - Closing the last 10 MB requires modifying cmix C++ to consume the 10
    sidecar feature streams (is_text, xml_stack, template_*, link_recency,
    article_hash, category_state, numeric_class, url_state) as additional
    context families. That work is not in this file.
  - The integer-quantized SSM context family (Phase 6 / sub-100 MB bet)
    is also not in this file. Pinned contract from prior turns:
    N=16 subsampled updates, 32-segment integer LUT softmax,
    fixed-seed PRNG weights, hidden state zeroed, truncated BPTT K=64,
    byte-level distribution.

Code budget: this wrapper is ~750 bytes. cmix binary is loaded from the
sibling cmix_wrapped program. For contest-honest score, the binary must
be inlined here too (~530 KB after base64+gzip); see meta.json.

Determinism: integer-only byte ops; cmix's own contract for the back-end.
Roundtrip is byte-exact by construction.
"""
from __future__ import annotations
import importlib.util as _u, pathlib as _p, sys as _s

T = [b'<text xml:space="preserve">', b"</text>", b"<page>", b"</page>",
     b"<revision>", b"</revision>", b"<contributor>", b"</contributor>",
     b"<timestamp>", b"</timestamp>", b"<username>", b"</username>",
     b"<comment>", b"</comment>", b"<title>", b"</title>", b"<id>", b"</id>",
     b"<minor />", b"{{", b"}}", b"[[Category:", b"[[Image:", b"[[", b"]]",
     b"&quot;", b"&lt;", b"&gt;", b"&amp;", b"http://", b"https://",
     b"<ref", b"</ref>", b"|thumb", b"|right", b"|left",
     b"Category:", b"File:", b"Image:"]
B = sorted(enumerate(T, 1), key=lambda x: -len(x[1]))
D = {i: t for i, t in enumerate(T, 1)}
_q = _p.Path(__file__).resolve().parent.parent / "cmix_wrapped" / "program.py"
_sp = _u.spec_from_file_location("_apex_cmix", _q)
_m = _u.module_from_spec(_sp); _s.modules[_sp.name] = _m; _sp.loader.exec_module(_m)


def _e(d):
    o = bytearray(); i = 0; n = len(d)
    while i < n:
        if d[i] == 0:
            o.extend((0, 255)); i += 1; continue
        for c, t in B:
            if d.startswith(t, i):
                o.extend((0, c)); i += len(t); break
        else:
            o.append(d[i]); i += 1
    return bytes(o)


def _d(d):
    o = bytearray(); i = 0; n = len(d)
    while i < n:
        b = d[i]
        if b:
            o.append(b); i += 1; continue
        c = d[i + 1]
        o.append(0) if c == 255 else o.extend(D[c])
        i += 2
    return bytes(o)


def compress(data): return _m.compress(_e(data))
def decompress(data): return _d(_m.decompress(data))
