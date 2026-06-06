from __future__ import annotations

import math
import struct

FULL = 1 << 32
HALF = 1 << 31
QTR = 1 << 30
TOT = 4096
LAST_STATS: dict[str, int] = {}


class BO:
    def __init__(self) -> None:
        self.o = bytearray()
        self.c = 0
        self.n = 0

    def w(self, b: int) -> None:
        self.c = (self.c << 1) | (b & 1)
        self.n += 1
        if self.n == 8:
            self.o.append(self.c)
            self.c = self.n = 0

    def f(self) -> bytes:
        if self.n:
            self.o.append((self.c << (8 - self.n)) & 255)
        return bytes(self.o)


class BI:
    def __init__(self, d: bytes) -> None:
        self.d = d
        self.i = self.c = self.n = 0

    def r(self) -> int:
        if self.n == 0:
            self.c = self.d[self.i] if self.i < len(self.d) else 0
            self.i += 1
            self.n = 8
        b = (self.c >> 7) & 1
        self.c = (self.c << 1) & 255
        self.n -= 1
        return b


class AE:
    def __init__(self) -> None:
        self.l = 0
        self.h = FULL - 1
        self.p = 0
        self.b = BO()

    def emit(self, b: int) -> None:
        self.b.w(b)
        while self.p:
            self.b.w(1 - b)
            self.p -= 1

    def bit(self, p: int, b: int) -> None:
        p = max(1, min(TOT - 1, p))
        c = 0 if b == 0 else TOT - p
        f = TOT - p if b == 0 else p
        r = self.h - self.l + 1
        self.h = self.l + (r * (c + f)) // TOT - 1
        self.l = self.l + (r * c) // TOT
        while True:
            if self.h < HALF:
                self.emit(0)
            elif self.l >= HALF:
                self.emit(1)
                self.l -= HALF
                self.h -= HALF
            elif self.l >= QTR and self.h < HALF + QTR:
                self.p += 1
                self.l -= QTR
                self.h -= QTR
            else:
                break
            self.l <<= 1
            self.h = (self.h << 1) | 1

    def fin(self) -> bytes:
        self.p += 1
        self.emit(0 if self.l < QTR else 1)
        return self.b.f()


class AD:
    def __init__(self, d: bytes) -> None:
        self.l = 0
        self.h = FULL - 1
        self.b = BI(d)
        self.c = 0
        for _ in range(32):
            self.c = (self.c << 1) | self.b.r()

    def bit(self, p: int) -> int:
        p = max(1, min(TOT - 1, p))
        r = self.h - self.l + 1
        x = ((self.c - self.l + 1) * TOT - 1) // r
        b = 0 if x < TOT - p else 1
        c = 0 if b == 0 else TOT - p
        f = TOT - p if b == 0 else p
        self.h = self.l + (r * (c + f)) // TOT - 1
        self.l = self.l + (r * c) // TOT
        while True:
            if self.h < HALF:
                pass
            elif self.l >= HALF:
                self.l -= HALF
                self.h -= HALF
                self.c -= HALF
            elif self.l >= QTR and self.h < HALF + QTR:
                self.l -= QTR
                self.h -= QTR
                self.c -= QTR
            else:
                break
            self.l <<= 1
            self.h = (self.h << 1) | 1
            self.c = (self.c << 1) | self.b.r()
        return b


class BM:
    def __init__(self) -> None:
        self.a = 1
        self.b = 1

    def p(self) -> int:
        return self.b * TOT // (self.a + self.b)

    def u(self, x: int) -> None:
        if x:
            self.b += 1
        else:
            self.a += 1
        if self.a + self.b > 2048:
            self.a = (self.a + 1) // 2
            self.b = (self.b + 1) // 2


def bc(b: int) -> int:
    if 65 <= b <= 90:
        return 1
    if 97 <= b <= 122:
        return 2
    if 48 <= b <= 57:
        return 3
    if b in (9, 10, 13, 32):
        return 4
    if b in (60, 62, 47, 34, 38, 59, 61):
        return 5
    if b in (91, 93, 123, 124, 125):
        return 6
    if b >= 128:
        return 7
    return 0


def fb(b: int) -> int:
    if 65 <= b <= 90:
        return b + 32
    if 97 <= b <= 122 or 48 <= b <= 57:
        return b
    if b in (32, 45, 95):
        return 32
    return 0


def hx(h: int, b: int) -> int:
    x = fb(b)
    return ((h * 131 + x) & 65535) if x else h


def stretch(p: int) -> float:
    x = max(1, min(TOT - 1, p)) / TOT
    return math.log(x / (1 - x)) / 8


def squash(x: float) -> int:
    if x <= -20:
        return 1
    if x >= 20:
        return TOT - 1
    return max(1, min(TOT - 1, int(TOT / (1 + math.exp(-x)))))


def lg(p: int) -> float:
    return math.log2(TOT / max(1, min(TOT - 1, p)))


class ST:
    def __init__(self) -> None:
        self.f = self.w = self.p = self.q = self.c = self.col = self.pc = 0
        self.bd = self.ld = self.slot = self.keying = 0
        self.th = self.kh = self.lh = self.ah = self.title = 0
        self.seen = 0
        self.rl = self.rc = 0
        self.tail = bytearray()

    def copy(self) -> "ST":
        z = ST.__new__(ST)
        z.__dict__ = self.__dict__.copy()
        z.tail = bytearray(self.tail)
        return z

    def seen_hit(self) -> int:
        h = self.lh or self.th or self.title
        return (self.seen >> (h & 63)) & 1

    def remember(self, h: int) -> None:
        if h:
            self.seen |= 1 << (h & 63)

    def cp(self) -> None:
        t = bytes(self.tail[-128:])
        if t.endswith(b"<title>"):
            self.f = 1
            self.title = 0
        elif t.endswith(b"</title>"):
            z = t.lower()
            self.pc = 2 if b"list of" in z else 3 if b"disambiguation" in z else 4
            self.ah = self.title
            self.remember(self.title)
            self.f = 0
        elif t.endswith(b"<id>"):
            self.f = 2
        elif t.endswith(b"</id>"):
            self.f = 0
        elif t.endswith(b"<timestamp>"):
            self.f = 3
        elif t.endswith(b"</timestamp>"):
            self.f = 0
        elif t.endswith(b"<username>"):
            self.f = 4
        elif t.endswith(b"</username>"):
            self.f = 0
        elif t.endswith(b"<comment>"):
            self.f = 5
        elif t.endswith(b"</comment>"):
            self.f = 0
        elif t.endswith(b'<text xml:space="preserve">'):
            self.f = 6
        elif t.endswith(b"</text>"):
            self.f = 0

    def keys(self, bp: int, pfx: int, pos: int) -> tuple:
        return (
            (0, bp, pfx),
            (1, bp, pfx, self.p),
            (2, bp, pfx, self.q, self.p),
            (3, bp, pfx, self.f, self.p),
            (4, bp, pfx, self.w, self.bd, self.ld, self.p),
            (5, bp, pfx, self.c, bc(self.p), self.rc, self.rl, self.f),
            (6, bp, pfx, self.col >> 3, self.f, self.w),
            (7, bp, pfx, self.pc, self.f, self.w, self.ah & 255),
            (8, bp, pfx, self.th & 255, self.kh & 255, self.slot & 7, self.w),
            (9, bp, pfx, self.lh & 255, self.title & 255, self.seen_hit()),
            (10, bp, pfx, (pos >> 8) & 31, self.f, self.c),
        )

    def up(self, b: int) -> None:
        if self.p == 91 and b == 91:
            self.w = 1
            self.ld = min(7, self.ld + 1)
            self.lh = 0
        elif self.p == 93 and b == 93:
            self.remember(self.lh)
            self.ld = max(0, self.ld - 1)
            self.w = 1 if self.ld else 0
        elif self.p == 123 and b == 123:
            self.w = 2
            self.bd = min(7, self.bd + 1)
            self.slot = self.keying = self.th = self.kh = 0
        elif self.p == 125 and b == 125:
            self.remember(self.th)
            self.bd = max(0, self.bd - 1)
            self.w = 2 if self.bd else 0
        elif self.p == 60 and b in (114, 82):
            self.w = 3
        elif self.w == 3 and b == 62:
            self.w = 0

        if self.w == 2:
            if b == 124:
                self.slot = min(15, self.slot + 1)
                self.keying = 1
                self.kh = 0
            elif b == 61 and self.keying == 1:
                self.keying = 2
            elif b not in (123, 125):
                if self.slot == 0:
                    self.th = hx(self.th, b)
                elif self.keying == 1:
                    self.kh = hx(self.kh, b)
        elif self.w == 1 and b not in (91, 93, 124):
            self.lh = hx(self.lh, b)
        if self.f == 1 and b not in (60, 47, 62):
            self.title = hx(self.title, b)

        self.tail.append(b)
        if len(self.tail) > 192:
            del self.tail[:64]
        self.cp()
        cl = bc(b)
        self.rl = min(15, self.rl + 1) if cl == self.rc else 1
        self.rc = self.c = cl
        self.col = 0 if b == 10 else min(255, self.col + 1)
        self.q, self.p = self.p, b


class COD:
    def __init__(self) -> None:
        self.m: dict[tuple, BM] = {}
        self.st = ST()
        self.last = (0, 0)
        self.reps = [1, 2, 4, 8]
        seed = [0.0, 0.45, 0.55, 0.45, 0.35, 0.35, 0.25, 0.25, 0.28, 0.3, 0.22, 0.18]
        self.w = [seed[:] for _ in range(8)]
        self.matches = 0
        self.literals = 0

    def model(self, k: tuple, create: bool = True) -> BM | None:
        m = self.m.get(k)
        if m is None and create:
            m = BM()
            self.m[k] = m
        return m

    def bitp(self, k: tuple) -> int:
        m = self.model(k)
        return m.p() if m is not None else TOT // 2

    def costbit(self, k: tuple, b: int) -> float:
        p = self.bitp(k)
        return lg(p if b else TOT - p)

    def encbit(self, ae: AE, k: tuple, b: int) -> None:
        m = self.model(k)
        assert m is not None
        ae.bit(m.p(), b)
        m.u(b)

    def decbit(self, ad: AD, k: tuple) -> int:
        m = self.model(k)
        assert m is not None
        b = ad.bit(m.p())
        m.u(b)
        return b

    def get_mix(self, st: ST, bp: int, pfx: int, pos: int, create: bool) -> tuple[int, list[BM], list[float]]:
        xs = [1.0]
        ms: list[BM] = []
        for k in st.keys(bp, pfx, pos):
            m = self.model(k, create)
            p = m.p() if m is not None else TOT // 2
            if m is not None:
                ms.append(m)
            xs.append(stretch(p))
        z = 0.0
        for wt, x in zip(self.w[bp], xs):
            z += wt * x
        return squash(z), ms, xs

    def update_mix(self, bp: int, bit: int, p: int, ms: list[BM], xs: list[float]) -> None:
        e = bit - p / TOT
        ww = self.w[bp]
        for i, x in enumerate(xs):
            v = ww[i] + 0.004 * e * x
            ww[i] = 8 if v > 8 else -8 if v < -8 else v
        for m in ms:
            m.u(bit)

    def lit_cost(self, st: ST, b: int, pos: int) -> float:
        pfx = 1
        c = 0.0
        for bp in range(8):
            bit = (b >> (7 - bp)) & 1
            p, _, _ = self.get_mix(st, bp, pfx, pos, False)
            c += lg(p if bit else TOT - p)
            pfx = (pfx << 1) | bit
        return c

    def lit_enc(self, ae: AE, b: int, pos: int) -> None:
        pfx = 1
        for bp in range(8):
            bit = (b >> (7 - bp)) & 1
            p, ms, xs = self.get_mix(self.st, bp, pfx, pos, True)
            ae.bit(p, bit)
            self.update_mix(bp, bit, p, ms, xs)
            pfx = (pfx << 1) | bit
        self.st.up(b)

    def lit_dec(self, ad: AD, pos: int) -> int:
        pfx = 1
        b = 0
        for bp in range(8):
            p, ms, xs = self.get_mix(self.st, bp, pfx, pos, True)
            bit = ad.bit(p)
            self.update_mix(bp, bit, p, ms, xs)
            b = (b << 1) | bit
            pfx = (pfx << 1) | bit
        self.st.up(b)
        return b

    def evkey(self) -> tuple:
        return ("e", self.st.f, self.st.w, self.st.c, self.last[0] >> 3, min(31, self.last[1]))

    def evcost(self, b: int) -> float:
        return self.costbit(self.evkey(), b)

    def evenc(self, ae: AE, b: int) -> None:
        self.encbit(ae, self.evkey(), b)

    def evdec(self, ad: AD) -> int:
        return self.decbit(ad, self.evkey())

    def uint_cost(self, v: int, n: int, tag: str) -> float:
        c = 0.0
        for i in range(n - 1, -1, -1):
            bit = (v >> i) & 1
            c += self.costbit((tag, n, i, self.st.f, self.st.w, self.last[0] >> 3), bit)
        return c

    def uint_enc(self, ae: AE, v: int, n: int, tag: str) -> None:
        for i in range(n - 1, -1, -1):
            self.encbit(ae, (tag, n, i, self.st.f, self.st.w, self.last[0] >> 3), (v >> i) & 1)

    def uint_dec(self, ad: AD, n: int, tag: str) -> int:
        v = 0
        for i in range(n - 1, -1, -1):
            v = (v << 1) | self.decbit(ad, (tag, n, i, self.st.f, self.st.w, self.last[0] >> 3))
        return v

    def mcost(self, l: int, d: int) -> float:
        db = d.bit_length() - 1
        lo = d - (1 << db)
        lc = min(254, l - 4)
        c = self.evcost(1) + self.uint_cost(lc, 8, "l")
        if d in self.reps:
            return c + self.uint_cost(1, 1, "rp") + self.uint_cost(self.reps.index(d), 2, "ri")
        return c + self.uint_cost(0, 1, "rp") + self.uint_cost(db, 5, "db") + self.uint_cost(lo, db, "lo")

    def menc(self, ae: AE, l: int, d: int) -> None:
        db = d.bit_length() - 1
        lo = d - (1 << db)
        lc = min(254, l - 4)
        self.evenc(ae, 1)
        self.uint_enc(ae, lc, 8, "l")
        if d in self.reps:
            self.uint_enc(ae, 1, 1, "rp")
            self.uint_enc(ae, self.reps.index(d), 2, "ri")
        else:
            self.uint_enc(ae, 0, 1, "rp")
            self.uint_enc(ae, db, 5, "db")
            self.uint_enc(ae, lo, db, "lo")
        if d in self.reps:
            self.reps.remove(d)
        self.reps = [d] + self.reps[:3]
        self.last = (l, db)
        self.matches += 1

    def mdec(self, ad: AD) -> tuple[int, int]:
        lc = self.uint_dec(ad, 8, "l")
        if self.uint_dec(ad, 1, "rp"):
            d = self.reps[self.uint_dec(ad, 2, "ri")]
            db = d.bit_length() - 1
        else:
            db = self.uint_dec(ad, 5, "db")
            lo = self.uint_dec(ad, db, "lo")
            d = (1 << db) + lo
        l = lc + 4
        if d in self.reps:
            self.reps.remove(d)
        self.reps = [d] + self.reps[:3]
        self.last = (l, db)
        self.matches += 1
        return l, d


def matches(d: bytes, i: int, tab: dict[bytes, list[int]]) -> list[tuple[int, int]]:
    a = tab.get(d[i : i + 4], ())
    r = []
    for j in a[-16:]:
        l = 4
        m = min(258, len(d) - i)
        while l < m and d[j + l] == d[i + l]:
            l += 1
        if l >= 6:
            r.append((l, i - j))
    r.sort(reverse=True)
    return r[:4]


def addpos(tab: dict[bytes, list[int]], d: bytes, i: int) -> None:
    if i + 4 <= len(d):
        k = d[i : i + 4]
        a = tab.setdefault(k, [])
        a.append(i)
        if len(a) > 48:
            del a[:-48]


def compress(d: bytes) -> bytes:
    ae = AE()
    c = COD()
    tab: dict[bytes, list[int]] = {}
    i = 0
    n = len(d)
    while i < n:
        best = None
        if i + 4 <= n:
            for l, dist in matches(d, i, tab):
                if l < 8:
                    continue
                lim = min(l, 16)
                ss = c.st.copy()
                lit = 0.0
                for q in range(lim):
                    lit += c.lit_cost(ss, d[i + q], i + q)
                    ss.up(d[i + q])
                mc = c.mcost(l, dist)
                if mc + 0.75 < lit and (best is None or mc - lit < best[0]):
                    best = (mc - lit, l, dist)
        if best is not None:
            _, l, dist = best
            c.menc(ae, l, dist)
            for q in range(i, i + l):
                c.st.up(d[q])
                addpos(tab, d, q)
            i += l
        else:
            c.evenc(ae, 0)
            c.lit_enc(ae, d[i], i)
            c.literals += 1
            addpos(tab, d, i)
            i += 1
    LAST_STATS.clear()
    LAST_STATS.update({"models": len(c.m), "matches": c.matches, "literals": c.literals})
    return struct.pack(">I", n) + ae.fin()


def decompress(a: bytes) -> bytes:
    n = struct.unpack(">I", a[:4])[0]
    ad = AD(a[4:])
    c = COD()
    o = bytearray()
    while len(o) < n:
        if c.evdec(ad) == 0:
            o.append(c.lit_dec(ad, len(o)))
            c.literals += 1
        else:
            l, dist = c.mdec(ad)
            p = len(o) - dist
            if p < 0:
                raise ValueError("bad distance")
            for _ in range(l):
                b = o[p]
                p += 1
                o.append(b)
                c.st.up(b)
    return bytes(o[:n])


def stats() -> dict[str, int]:
    return dict(LAST_STATS)
