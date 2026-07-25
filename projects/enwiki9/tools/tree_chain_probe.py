import math
import sys

def bc(b):
    if 65<=b<=90:return 1
    if 97<=b<=122:return 2
    if 48<=b<=57:return 3
    if b in (9,10,13,32):return 4
    if b in (60,62,47,34,38,59):return 5
    if b in (91,93,123,124,125):return 6
    if b>=128:return 7
    return 0

class ST:
    def __init__(s):
        s.f=0;s.p=0;s.c=0;s.tail=bytearray();s.h=[0,0,0]
    def cp(s):
        t=bytes(s.tail[-96:])
        if t.endswith(b"<title>"):s.f=1
        elif t.endswith(b"</title>"):s.f=0
        elif t.endswith(b"<id>"):s.f=2
        elif t.endswith(b"</id>"):s.f=0
        elif t.endswith(b"<timestamp>"):s.f=3
        elif t.endswith(b"</timestamp>"):s.f=0
        elif t.endswith(b"<username>"):s.f=4
        elif t.endswith(b"</username>"):s.f=0
        elif t.endswith(b"<comment>"):s.f=5
        elif t.endswith(b"</comment>"):s.f=0
        elif t.endswith(b'<text xml:space="preserve">'):s.f=6
        elif t.endswith(b"</text>"):s.f=0
    def up(s,b):
        s.tail.append(b)
        if len(s.tail)>192:del s.tail[:64]
        s.cp()
        s.h.append(b)
        s.h.pop(0)
        s.p=b;s.c=bc(b)
    def ctx_key(s):
        return (tuple(s.h), s.f, s.c)

class CM:
    def __init__(s, n):
        s.c = [1]*n; s.t = n
    def cost(s, x):
        return -math.log2(s.c[x]/s.t)
    def up(s, x):
        s.c[x] += 1; s.t += 1
        if s.t > 4096:
            s.t = 0
            for i in range(len(s.c)):
                s.c[i] = (s.c[i]+1)//2
                s.t += s.c[i]

class TOK_V6:
    def __init__(s):
        s.e = CM(2); s.l = {}; s.d = {}; s.lo = {}; s.last = (0,0)
    def mc(s, L, D):
        db = D.bit_length()-1; lo = D-(1<<db); lb = min(254, L-4)
        lk = (s.last[1], min(31, s.last[0]//8))
        dk = (min(31, L//8), s.last[1])
        lm = s.l.setdefault(lk, CM(255))
        dm = s.d.setdefault(dk, CM(32))
        return s.e.cost(1) + lm.cost(lb) + dm.cost(db) + db
    def update(s, L, D):
        db = D.bit_length()-1; lo = D-(1<<db); lb = min(254, L-4)
        lk = (s.last[1], min(31, s.last[0]//8))
        dk = (min(31, L//8), s.last[1])
        s.e.up(1)
        s.l.setdefault(lk, CM(255)).up(lb)
        s.d.setdefault(dk, CM(32)).up(db)
        s.last = (L, db)
    def lc(s): return s.e.cost(0)
    def up_lit(s): s.e.up(0); s.last = (0, s.last[1])

def add_global(tab, d, i):
    if i+4 <= len(d):
        k = d[i:i+4]
        a = tab.setdefault(k, [])
        a.append(i)
        if len(a) > 64: del a[:-64]

def get_global_match(d, i, tab):
    best_L = 0; best_D = 0
    k = d[i:i+4]
    for j in reversed(tab.get(k, [])):
        if i <= j: continue
        L = 4
        m = min(258, len(d)-i)
        while L < m and d[j+L] == d[i+L]: L += 1
        if L > best_L:
            best_L = L; best_D = i - j
    return best_L, best_D

def run_probe(limit):
    with open("data/enwik9", "rb") as f:
        d = f.read(limit)
    
    st = ST()
    tree_chain = {}
    global_tab = {}
    v6 = TOK_V6()
    
    m_event = {}
    m_idx = {}
    m_len = {}
    
    total_v6_match_bits = 0.0
    total_tc_match_bits = 0.0
    
    total_v6_dist_bits = 0.0
    total_tc_idx_bits = 0.0
    total_tc_len_bits = 0.0
    
    bytes_covered_tc = 0
    bytes_covered_global = 0
    
    i = 0
    n = len(d)
    
    while i < n:
        ctx = st.ctx_key()
        chain = tree_chain.get(ctx, [])
        
        tc_L = 0; tc_idx = 0; tc_pos = 0
        for j, pos in enumerate(reversed(chain)):
            L = 0
            m = min(258, n - i)
            while L < m and d[pos+L] == d[i+L]: L += 1
            if L > tc_L:
                tc_L = L; tc_idx = j; tc_pos = pos
        
        g_L, g_D = get_global_match(d, i, global_tab)
        
        if tc_L >= 4:
            tc_D = i - tc_pos
            
            ev_mod = m_event.setdefault(ctx, CM(2))
            idx_mod = m_idx.setdefault(ctx, CM(16))
            len_mod = m_len.setdefault((ctx, tc_idx), CM(255))
            
            ev_cost = ev_mod.cost(1)
            idx_cost = idx_mod.cost(tc_idx)
            len_cost = len_mod.cost(min(254, tc_L - 4))
            
            tc_match_cost = ev_cost + idx_cost + len_cost
            
            # v6 cost for same match length/distance
            v6_match_cost = v6.mc(tc_L, tc_D)
            v6_dist_cost = v6_match_cost - v6.lc() # rough approx of dist+len tokens
            
            total_tc_match_bits += tc_match_cost
            total_v6_match_bits += v6_match_cost
            
            total_tc_idx_bits += idx_cost
            total_tc_len_bits += len_cost
            
            # What would v6 dist bits be exactly?
            db = tc_D.bit_length() - 1
            v6_dist_bits = v6.d.setdefault((min(31, tc_L//8), v6.last[1]), CM(32)).cost(db) + db
            total_v6_dist_bits += v6_dist_bits
            
            bytes_covered_tc += tc_L
            if g_L >= 4:
                bytes_covered_global += tc_L # Since we took the tc match, it covers this many bytes. 
                                             # A true optimal parser would differ, but let's just track potential.
            
            ev_mod.up(1)
            idx_mod.up(tc_idx)
            len_mod.up(min(254, tc_L - 4))
            v6.update(tc_L, tc_D)
            
            for q in range(i, i + tc_L):
                q_ctx = st.ctx_key()
                c = tree_chain.setdefault(q_ctx, [])
                c.append(q)
                if len(c) > 16: c.pop(0)
                st.up(d[q])
                add_global(global_tab, d, q)
                
            i += tc_L
        else:
            if g_L >= 4:
                bytes_covered_global += g_L
                
            ev_mod = m_event.setdefault(ctx, CM(2))
            ev_mod.up(0)
            v6.up_lit()
            
            c = tree_chain.setdefault(ctx, [])
            c.append(i)
            if len(c) > 16: c.pop(0)
            st.up(d[i])
            add_global(global_tab, d, i)
            i += 1

    print(f"Results for {limit//1024}KB:")
    print(f"Match coverage: TC = {bytes_covered_tc} bytes, Global (potential) = {bytes_covered_global} bytes")
    print(f"Total TC Match Bits: {total_tc_match_bits:.1f}")
    print(f"Total v6 Match Bits: {total_v6_match_bits:.1f}")
    print(f"  TC Index Bits: {total_tc_idx_bits:.1f}")
    print(f"  v6 Dist Bits : {total_v6_dist_bits:.1f}")
    
    if total_v6_match_bits > 0:
        reduction = (total_v6_match_bits - total_tc_match_bits) / total_v6_match_bits * 100
        print(f"Reduction in match token bits: {reduction:.2f}%")

run_probe(100 * 1024)
run_probe(1024 * 1024)
