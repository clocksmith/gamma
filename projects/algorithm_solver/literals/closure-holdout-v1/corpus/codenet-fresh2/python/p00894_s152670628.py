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
        n = I()
        if n == 0:
            break
        a = [LS() for _ in range(n)]
        d = {}
        e = collections.defaultdict(int)
        b = []
        for day,ts,f,i in a:
            i = int(i)
            ta = ts.split(':')
            t = int(ta[0]) * 60 + int(ta[1])
            if i == 0:
                if f == 'I':
                    for k in list(d.keys()):
                        e[k] -= t - d[k]
                    d[i] = t
                else:
                    del d[i]
                    for k in list(d.keys()):
                        e[k] += t - d[k]
            else:
                if f == 'I':
                    d[i] = t
                else:
                    if 0 in d:
                        e[i] += t - d[i]
                    del d[i]
        if len(e) == 0:
            rr.append(0)
        else:
            rr.append(max(e.values()))

    return '\n'.join(map(str,rr))


print(main())


