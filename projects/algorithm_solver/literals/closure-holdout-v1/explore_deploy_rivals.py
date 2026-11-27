#!/usr/bin/env python3
"""POST HOC (fresh2, repositories) and DEVELOPMENT (dev). Two checks for the plain-language summary.

    python3 -I explore_deploy_rivals.py

1. GreedTok (Lim et al. 2025, Algorithms 1-3, as implemented in fixed-source-v3/engine.c) and PathPiece-style pruning
   (engine.c) against BPE at 84 and 3,924 fragments, exact parser, on the Study 2 sets (already scored: post hoc).
2. On dev at 3,924 fragments: BPE, exact open and exact pair-only under the exact parser, greedy longest-match, and
   BPE's own merge replay. Writes out/posthoc-deploy-rivals.json.
"""
import json, sys
from pathlib import Path
LIT = Path(__file__).resolve().parent.parent; OH = LIT/'objective-holdout-v1'; CL = LIT/'closure-holdout-v1'
sys.path.insert(0, str(OH)); import bits_oh as B
def chain(p): return [bytes.fromhex(l.split()[5]) for l in Path(p).read_text().splitlines() if l.startswith('E ') and len(l.split())==6]
def load(spec, root): return [(root/f['path']).read_bytes() for f in json.loads(spec.read_text())['files']]
fz = json.loads((CL/'frozen/dictionaries.json').read_text()); A = fz['alphabet']
bpe = [bytes.fromhex(h) for h in fz['dictionaries']['bpe-K4096']]; singles = bpe[:A]
C = LIT/'codenet-replication-v1/chains/primary/s1-whole'
gt = chain(C/'both-L16-greedtok.txt'); pp = chain(C/'both-L16-pathpiece.txt')
def frag(order): return [e for e in order if len(e) > 1]
sets = {'fresh2': (CL/'sets/fresh2.json', CL), 'project-python': (CL/'sets/project-python.json', CL), 'project-javascript': (CL/'sets/project-javascript.json', CL)}
def tok(entries, docs):
    d = B.Dictionary(entries); return sum(len(B.parse_tokens(d.edges(r))) for r in docs)
RES = {'rivals_vs_bpe_pct': {}, 'dev_3924': {}}
for s, (sp, r) in sets.items():
    docs = load(sp, r); out = []; RES['rivals_vs_bpe_pct'][s] = {}
    for k in (84, 3924):
        b = tok(singles + bpe[A:A+k], docs)
        for n, o in (('GreedTok', gt), ('PathPiece-style', pp)):
            f = frag(o)
            v = round(100*(tok(singles+f[:k], docs)/b-1), 2) if len(f) >= k else None
            RES['rivals_vs_bpe_pct'][s][f'{n}@{k}'] = v
            out.append(f'{n}@{k} {v}')
    print(s, ' | '.join(out), flush=True)
# Longest-match on dev at 3,924 fragments, plus BPE merge replay
dev = load(OH/'frozen/sets/dev.json', LIT)
def lm(entries, docs):
    S = set(entries); L = max(map(len, entries)); n = 0
    for raw in docs:
        i = 0
        while i < len(raw):
            for l in range(min(L, len(raw)-i), 0, -1):
                if raw[i:i+l] in S or l == 1: i += l; n += 1; break
    return n
merges = []; seen = 0
for line in (C/'both-L16-bpe.txt').read_text().splitlines():
    p = line.split()
    if p and p[0] == 'E':
        seen += 1
        if seen == A + 3924: break
    elif p and p[0] == 'M': merges.append((bytes.fromhex(p[1]), bytes.fromhex(p[2])))
rank = {}
for i, pr in enumerate(merges): rank.setdefault(pr, i)
def mr(docs):
    n = 0
    for raw in docs:
        t = [bytes([x]) for x in raw]
        while len(t) > 1:
            best = None; br = 10**9
            for i in range(len(t)-1):
                q = rank.get((t[i], t[i+1]))
                if q is not None and q < br: br, best = q, (t[i], t[i+1])
            if best is None: break
            u = []; i = 0
            while i < len(t):
                if i+1 < len(t) and (t[i], t[i+1]) == best: u.append(t[i]+t[i+1]); i += 2
                else: u.append(t[i]); i += 1
            t = u
        n += len(t)
    return n
E = CL/'out/exact'
arms = {'BPE': singles + bpe[A:A+3924], 'open (exact)': singles + frag(chain(E/'exact-entry-s1-whole.txt'))[:3924],
        'pair-only = normalized (exact)': singles + frag(chain(E/'exact-closed-s1-whole.txt'))[:3924]}
ref = {'exact': tok(arms['BPE'], dev), 'longest-match': lm(arms['BPE'], dev), 'BPE merge replay': mr(dev)}
print('dev BPE:', ref); RES['dev_3924']['BPE'] = ref
for a, e in arms.items():
    x, y = tok(e, dev), lm(e, dev)
    RES['dev_3924'][a] = {'exact': x, 'longest_match': y}
    print(f'dev {a}: exact {x} ({100*(x/ref["exact"]-1):+.2f}% vs BPE exact) | longest-match {y} ({100*(y/ref["longest-match"]-1):+.2f}% vs BPE longest-match, {100*(y/ref["BPE merge replay"]-1):+.2f}% vs BPE merge replay)')
(LIT/'closure-holdout-v1'/'out'/'posthoc-deploy-rivals.json').write_text(json.dumps(RES, indent=1) + '\n')
