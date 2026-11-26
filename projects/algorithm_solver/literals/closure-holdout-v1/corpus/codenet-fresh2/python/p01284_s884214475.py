import math,string,itertools,fractions,heapq,collections,re,array,bisect,sys,random,time,copy,functools

sys.setrecursionlimit(10**7)
inf = 10**20
eps = 1.0 / 10**10
mod = 10**9+7
dd = [(0,-1),(1,0),(0,1),(-1,0)]
ddn = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,-1),(-1,0),(-1,1)]

def LI(): return [int(x) for x in sys.stdin.readline().split()]
def LI_(): return [int(x)-1 for x in sys.stdin.readline().split()]
def LF(): return [float(x) for x in sys.stdin.readline().split()]
def LS(): return sys.stdin.readline().split()
def I(): return int(sys.stdin.readline())
def F(): return float(sys.stdin.readline())
def S(): return input()
def pf(s): return print(s, flush=True)


def main():
    rr = []

    while True:
        T = I()
        if T == 0:
            break
        t = LI()
        n = I()
        a = sorted([LI() for _ in range(n)])
        ad = collections.defaultdict(lambda: inf)
        for d,m in a:
            if ad[d] > m:
                ad[d] = m
        c = collections.defaultdict(lambda: inf)
        c[-1] = 0
        cd = 0
        for d in range(1,max(ad.keys()) + 1):
            m = ad[d]
            nt = 1
            nd = collections.defaultdict(lambda: inf)
            for k,v in c.items():
                if t[(k+nt) % T] <= m:
                    if nd[(k+nt) % T] > v:
                        nd[(k+nt) % T] = v
                if nd[0] > v+1:
                    nd[0] = v+1
            c = nd
            cd = d
        rr.append(min(c.values()))


    return '\n'.join(map(str,rr))


print(main())


