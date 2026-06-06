"""xml_skel_wordcode_bz2_min_v1 — typed XML + wordcode + bz2 (compact)."""
from __future__ import annotations
import bz2, hashlib, re, struct

V = 1
T, L = 0, 1  # mode tags: typed, literal
S = [b"\x00\x00\xFE\xF1", b"\x00\x00\xFE\xF2", b"\x00\x00\xFE\xF4",
     b"\x00\x00\xFE\xF5", b"\x00\x00\xFE\xF6", b"\x00\x00\xFE\xF8"]
N = ["title", "id", "timestamp", "username", "ip", "comment"]
R = [
    re.compile(rb"(<comment>)(.*?)(</comment>)", re.DOTALL),
    re.compile(rb"(<title>)([^<]*)(</title>)"),
    re.compile(rb"(<timestamp>)([^<]*)(</timestamp>)"),
    re.compile(rb"(<username>)([^<]*)(</username>)"),
    re.compile(rb"(<ip>)([^<]*)(</ip>)"),
    re.compile(rb"(<id>)([^<]*)(</id>)"),
]
RI = [5, 0, 2, 3, 4, 1]  # apply order: comment first; index into N
WE = 0x02
WC = 0x80
WK = 128
WW = re.compile(rb"[A-Za-z]{3,32}")


def _h(d): return hashlib.sha256(d).digest()


def _ext(d):
    sc = d
    ch = [[] for _ in N]
    for i, rx in enumerate(R):
        ni = RI[i]
        cap = ch[ni]
        sn = S[ni]
        def rp(m, c=cap, s=sn):
            c.append(m.group(2))
            return m.group(1) + s + m.group(3)
        sc = rx.sub(rp, sc)
    return sc, ch


def _rea(sc, ch):
    it = [iter(c) for c in ch]
    o = bytearray()
    p = 0
    n = len(sc)
    while p < n:
        m = -1
        if p + 4 <= n:
            w = sc[p:p + 4]
            for i, s in enumerate(S):
                if w == s:
                    m = i
                    break
        if m < 0:
            o.append(sc[p])
            p += 1
        else:
            o.extend(next(it[m]))
            p += 4
    return bytes(o)


def _sa(vs):
    o = bytearray(struct.pack(">I", len(vs)))
    for v in vs:
        o.extend(struct.pack(">I", len(v)))
        o.extend(v)
    return bytes(o)


def _pa(b):
    p = 0
    (n,) = struct.unpack(">I", b[p:p + 4]); p += 4
    o = []
    for _ in range(n):
        (L,) = struct.unpack(">I", b[p:p + 4]); p += 4
        o.append(b[p:p + L]); p += L
    return o


def _wp(d):
    cn = {}
    for m in WW.finditer(d):
        w = m.group(0)
        cn[w] = cn.get(w, 0) + 1
    sc = []
    for w, f in cn.items():
        if f < 2: continue
        s = f * (len(w) - 1) - (1 + len(w))
        if s > 0: sc.append((s, w))
    sc.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in sc[:WK]]


def _esc(c):
    if not any(b == WE or b >= WC for b in c): return c
    o = bytearray()
    for b in c:
        if b == WE or b >= WC: o.append(WE)
        o.append(b)
    return bytes(o)


def _sub(d, ws):
    if not ws: return _esc(d)
    cm = {w: bytes([WC + i]) for i, w in enumerate(ws)}
    pt = re.compile(b"|".join(re.escape(w) for w in ws))
    pr = []
    p = 0
    for m in pt.finditer(d):
        if m.start() > p: pr.append(_esc(d[p:m.start()]))
        pr.append(cm[m.group(0)])
        p = m.end()
    if p < len(d): pr.append(_esc(d[p:]))
    return b"".join(pr)


def _exp(st, ws):
    o = bytearray()
    p = 0
    n = len(st)
    while p < n:
        b = st[p]
        if b == WE:
            p += 1; o.append(st[p]); p += 1
        elif b >= WC:
            o.extend(ws[b - WC]); p += 1
        else:
            o.append(b); p += 1
    return bytes(o)


def _wcp(d):
    ws = _wp(d)
    bd = _sub(d, ws)
    h = bytearray()
    h.append(len(ws))
    for w in ws:
        h.append(len(w))
        h.extend(w)
    return struct.pack(">I", len(h)) + bytes(h) + bd


def _wcu(p):
    (hl,) = struct.unpack(">I", p[:4])
    h = p[4:4 + hl]
    bd = p[4 + hl:]
    k = h[0]
    o = 1
    ws = []
    for _ in range(k):
        L = h[o]; o += 1
        ws.append(h[o:o + L]); o += L
    return _exp(bd, ws)


def _build(mode, body, n, hh):
    head = struct.pack(">BBQ", V, mode, n) + hh
    return head + bz2.compress(body, 9)


def _open(a):
    v, mode, n = struct.unpack(">BBQ", a[:10])
    if v != V: raise ValueError("version")
    hh = a[10:42]
    body = bz2.decompress(a[42:])
    return mode, n, hh, body


def compress(data):
    n = len(data)
    hh = _h(data)
    if any(s in data for s in S):
        return _build(L, data, n, hh)
    sc, ch = _ext(data)
    if _rea(sc, ch) != data:
        return _build(L, data, n, hh)
    ps = _wcp(sc)
    if _wcu(ps) != sc:
        return _build(L, data, n, hh)
    body = bytearray(struct.pack(">I", len(ps)))
    body.extend(ps)
    for i in range(6):
        sa = _sa(ch[i])
        body.extend(struct.pack(">I", len(sa)))
        body.extend(sa)
    return _build(T, bytes(body), n, hh)


def decompress(arch):
    mode, n, hh, body = _open(arch)
    if mode == L:
        out = body
    else:
        p = 0
        (sl,) = struct.unpack(">I", body[p:p + 4]); p += 4
        ps = body[p:p + sl]; p += sl
        sc = _wcu(ps)
        ch = []
        for _ in range(6):
            (al,) = struct.unpack(">I", body[p:p + 4]); p += 4
            ch.append(_pa(body[p:p + al])); p += al
        out = _rea(sc, ch)
    if len(out) != n: raise ValueError("size")
    if _h(out) != hh: raise ValueError("hash")
    return out
