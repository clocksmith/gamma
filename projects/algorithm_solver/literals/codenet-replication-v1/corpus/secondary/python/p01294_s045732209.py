import math,string,itertools,fractions,heapq,collections,re,array,bisect,sys,random,time,copy,functools

sys.setrecursionlimit(10**7)
inf = 10**20
eps = 1.0 / 10**10
mod = 10**9+7
dd = [(-1,0),(0,1),(1,0),(0,-1)]
ddn = [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]

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
        n,d = LI()
        if n == 0:
            break

        a = [LI()[1:] for _ in range(n)]
        q = []
        sa = []
        for ai in a:
            s = sum(ai)
            sa.append([s, ai])

        f = True
        while f:
            f = False
            sa.sort()
            ls,la = sa[-1]
            if ls == 0:
                break
            ls2 = sa[-2][0]
            if ls - la[-1] >= ls2 - d:
                sa[-1] = [ls - la[-1], la[:-1]]
                f = True
                continue

            for i in range(n-2,-1,-1):
                ts, ta = sa[i]
                if ts == 0:
                    break
                if ts - ta[-1] >= ls - d:
                    sa[i] = [ts - ta[-1], ta[:-1]]
                    f = True

        if sa[-1][0] == 0:
            rr.append('Yes')
        else:
            rr.append('No')

    return '\n'.join(map(str,rr))



print(main())

