import math,string,itertools,fractions,heapq,collections,re,array,bisect,sys,random,time,copy,functools

sys.setrecursionlimit(10**7)
inf = 10**20
eps = 1.0 / 10**10
mod = 998244353
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
    mk = {}
    mk['T'] = 10
    mk['J'] = 11
    mk['Q'] = 12
    mk['K'] = 13
    mk['A'] = 14
    for i in range(1,10):
        mk[str(i)] = i

    while True:
        t = S()
        if t == '#':
            break
        a = [list(map(lambda x: (mk[x[0]], x[1]), LS())) for _ in range(4)]
        d = 0
        ns = 0
        ew = 0
        for i in range(13):
            m = -1
            mi = -1
            it = a[d][i][1]
            for j in range(4):
                k = a[j][i][0]
                if a[j][i][1] == t:
                    k += 100
                if a[j][i][1] == it:
                    k += 50
                if m < k:
                    m = k
                    mi = j
            d = mi
            if mi % 2 == 0:
                ns += 1
            else:
                ew += 1
        if ns > 6:
            rr.append('NS {}'.format(ns - 6))
        else:
            rr.append('EW {}'.format(ew - 6))

    return '\n'.join(map(str, rr))


print(main())


