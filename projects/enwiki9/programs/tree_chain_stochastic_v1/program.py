import math, struct

FULL = 1 << 32
HALF = 1 << 31
QTR = 1 << 30
TOT = 4096

class BO:
    def __init__(s): s.o = bytearray(); s.c = 0; s.n = 0
    def w(s, b):
        s.c = (s.c << 1) | (b & 1); s.n += 1
        if s.n == 8: s.o.append(s.c); s.c = 0; s.n = 0
    def f(s):
        if s.n: s.o.append((s.c << (8 - s.n)) & 255)
        return bytes(s.o)

class BI:
    def __init__(s, d): s.d = d; s.i = 0; s.c = 0; s.n = 0
    def r(s):
        if s.n == 0:
            s.c = s.d[s.i] if s.i < len(s.d) else 0; s.i += 1; s.n = 8
        b = (s.c >> 7) & 1; s.c = (s.c << 1) & 255; s.n -= 1; return b

class AE:
    def __init__(s): s.l = 0; s.h = FULL - 1; s.p = 0; s.b = BO()
    def emit(s, b):
        s.b.w(b)
        while s.p: s.b.w(1 - b); s.p -= 1
    def bit(s, p, b):
        p = max(1, min(TOT - 1, p)); c = 0 if b == 0 else TOT - p; f = TOT - p if b == 0 else p; r = s.h - s.l + 1
        s.h = s.l + (r * (c + f)) // TOT - 1; s.l = s.l + (r * c) // TOT
        while 1:
            if s.h < HALF: s.emit(0)
            elif s.l >= HALF: s.emit(1); s.l -= HALF; s.h -= HALF
            elif s.l >= QTR and s.h < HALF + QTR: s.p += 1; s.l -= QTR; s.h -= QTR
            else: break
            s.l <<= 1; s.h = (s.h << 1) | 1
    def fin(s): s.p += 1; s.emit(0 if s.l < QTR else 1); return s.b.f()

class AD:
    def __init__(s, d):
        s.l = 0; s.h = FULL - 1; s.b = BI(d); s.c = 0
        for _ in range(32): s.c = (s.c << 1) | s.b.r()
    def bit(s, p):
        p = max(1, min(TOT - 1, p)); r = s.h - s.l + 1; x = ((s.c - s.l + 1) * TOT - 1) // r; b = 0 if x < TOT - p else 1
        c = 0 if b == 0 else TOT - p; f = TOT - p if b == 0 else p
        s.h = s.l + (r * (c + f)) // TOT - 1; s.l = s.l + (r * c) // TOT
        while 1:
            if s.h < HALF: pass
            elif s.l >= HALF: s.l -= HALF; s.h -= HALF; s.c -= HALF
            elif s.l >= QTR and s.h < HALF + QTR: s.l -= QTR; s.h -= QTR; s.c -= QTR
            else: break
            s.l <<= 1; s.h = (s.h << 1) | 1; s.c = (s.c << 1) | s.b.r()
        return b

class BM:
    def __init__(s): s.a = 1; s.b = 1
    def p(s): return s.b * TOT // (s.a + s.b)
    def u(s, x):
        if x: s.b += 1
        else: s.a += 1
        if s.a + s.b > 2048: s.a = (s.a + 1) // 2; s.b = (s.b + 1) // 2

class TreeModel:
    def __init__(s):
        s.nodes = {}
    def get_prob(s, ctx):
        if ctx not in s.nodes: s.nodes[ctx] = BM()
        return s.nodes[ctx]

def encode_val(ae, model, ctx, val, bits):
    for i in range(bits - 1, -1, -1):
        b = (val >> i) & 1
        m = model.get_prob((ctx, i))
        ae.bit(m.p(), b)
        m.u(b)

def decode_val(ad, model, ctx, bits):
    val = 0
    for i in range(bits - 1, -1, -1):
        m = model.get_prob((ctx, i))
        b = ad.bit(m.p())
        m.u(b)
        val = (val << 1) | b
    return val

MAX_CHAIN = 16
MIN_LEN = 3

def compress(d):
    ae = AE()
    tm = TreeModel()
    tree_chain = {}
    i = 0
    n = len(d)
    
    while i < n:
        ctx = tuple(d[max(0, i-3):i])
        chain = tree_chain.get(ctx, [])
        
        best_len = 0
        best_idx = 0
        
        for idx, pos in enumerate(reversed(chain)):
            L = 0
            lim = min(n - i, 255 + MIN_LEN)
            while L < lim and d[pos + L] == d[i + L]:
                L += 1
            if L > best_len:
                best_len = L
                best_idx = idx
                if L == lim: break
                
        if best_len >= MIN_LEN:
            m_match = tm.get_prob(('match', ctx))
            ae.bit(m_match.p(), 1)
            m_match.u(1)
            
            encode_val(ae, tm, ('idx', ctx), best_idx, 4)
            encode_val(ae, tm, ('len', ctx, best_idx), best_len - MIN_LEN, 8)
            
            for q in range(i, i + best_len):
                q_ctx = tuple(d[max(0, q-3):q])
                c = tree_chain.setdefault(q_ctx, [])
                c.append(q)
                if len(c) > MAX_CHAIN: c.pop(0)
            
            i += best_len
        else:
            m_match = tm.get_prob(('match', ctx))
            ae.bit(m_match.p(), 0)
            m_match.u(0)
            
            encode_val(ae, tm, ('lit', ctx), d[i], 8)
            
            c = tree_chain.setdefault(ctx, [])
            c.append(i)
            if len(c) > MAX_CHAIN: c.pop(0)
            
            i += 1
            
    return struct.pack(">I", n) + ae.fin()

def decompress(a):
    n = struct.unpack(">I", a[:4])[0]
    ad = AD(a[4:])
    tm = TreeModel()
    tree_chain = {}
    o = bytearray()
    
    while len(o) < n:
        i = len(o)
        ctx = tuple(o[max(0, i-3):i])
        chain = tree_chain.get(ctx, [])
        
        m_match = tm.get_prob(('match', ctx))
        is_match = ad.bit(m_match.p())
        m_match.u(is_match)
        
        if is_match:
            best_idx = decode_val(ad, tm, ('idx', ctx), 4)
            best_len = decode_val(ad, tm, ('len', ctx, best_idx), 8) + MIN_LEN
            
            pos = chain[len(chain) - 1 - best_idx]
            
            for _ in range(best_len):
                b = o[pos]
                pos += 1
                o.append(b)
                
                q = len(o) - 1
                q_ctx = tuple(o[max(0, q-3):q])
                c = tree_chain.setdefault(q_ctx, [])
                c.append(q)
                if len(c) > MAX_CHAIN: c.pop(0)
        else:
            b = decode_val(ad, tm, ('lit', ctx), 8)
            o.append(b)
            
            c = tree_chain.setdefault(ctx, [])
            c.append(i)
            if len(c) > MAX_CHAIN: c.pop(0)
            
    return bytes(o)
