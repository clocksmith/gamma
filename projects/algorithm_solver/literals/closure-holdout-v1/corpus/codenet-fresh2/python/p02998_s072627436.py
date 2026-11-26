import sys
sys.setrecursionlimit(10**7)
INF = 10 ** 18
MOD = 10 ** 9 + 7
def YesNo(x): return 'Yes' if x else 'No'
def LI(): return [int(x) for x in sys.stdin.readline().split()]
def LI_(): return [int(x) - 1 for x in sys.stdin.readline().split()]
def LF(): return [float(x) for x in sys.stdin.readline().split()]
def LS(): return sys.stdin.readline().split()
def II(): return int(sys.stdin.readline())
def SI(): return input()
from collections import defaultdict

def main():
    N = II()
    xy = []
    for _ in range(N):
        xy.append(LI())
    xy2g = defaultdict(int)
    g2xy = defaultdict(set)
    for x, y in xy:
        y = -y
        gx = xy2g[x]
        gy = xy2g[y]
        if gx == gy != 0:
            continue
        elif gx != 0 and gy != 0:  # merge
            if len(g2xy[gx]) < len(g2xy[gy]):
                gx, gy = gy, gx
            for xy in g2xy[gy]:
                xy2g[xy] = gx
            g2xy[gx] |= g2xy[gy]
            g2xy[gy].clear()
        else:
            g = gx or gy or x
            xy2g[x] = xy2g[y] = g
            g2xy[g] |= {x, y}
    ans = -N
    for xys in g2xy.values():
        nx = sum(xy > 0 for xy in xys)
        ny = len(xys) - nx
        ans += nx * ny
    return ans

print(main())