import sys
input=lambda :sys.stdin.readline().rstrip()
sys.setrecursionlimit(10**8)

class LCA(object):
    def __init__(self, to, root=0):
        self.__n = len(to)
        self.__to = to
        self.__logn = (self.__n - 1).bit_length()
        self.__depth = [-1] * self.__n
        self.__dist = [-1] * self.__n
        self.__depth[root] = 0
        self.__dist[root] = 0
        self.__parents = [[-1] * self.__n for _ in range(self.__logn)]
        self.__dfs(root)
        self.__doubling()

    def __dfs(self, v):
        for u, c, d in self.__to[v]:
            if self.__depth[u] != -1: continue
            self.__parents[0][u] = v
            self.__depth[u] = self.__depth[v] + 1
            self.__dist[u] = self.__dist[v] + d
            self.__dfs(u)

    def __doubling(self):
        for i in range(1, self.__logn):
            for v in range(self.__n):
                if self.__parents[i - 1][v] == -1: continue
                self.__parents[i][v] = self.__parents[i - 1][self.__parents[i - 1][v]]

    @property
    def depth(self):
        return self.__depth

    @property
    def dist(self):
        return self.__dist

    def get(self, u, v):
        dd = self.__depth[v] - self.__depth[u]
        if dd < 0:
            u, v = v, u
            dd *= -1
        for i in range(self.__logn):
            if dd & (2 ** i):
                v = self.__parents[i][v]
        if v == u: return v
        for i in range(self.__logn - 1, -1, -1):
            pu = self.__parents[i][u]
            pv = self.__parents[i][v]
            if pu != pv: u, v = pu, pv
        return self.__parents[0][u]

def resolve():
    n, q = map(int, input().split())
    to = [[] for _ in range(n)]
    for _ in range(n-1):
        a, b, c, d = map(int, input().split())
        a -= 1; b -= 1
        to[a].append((b, c, d))
        to[b].append((a, c, d))

    G = LCA(to)
    Query = [[] for _ in range(n)]
    for i in range(q):
    # idx, color, mag, coef
        x, y, u, v = map(int, input().split())
        u -= 1; v -= 1
        c = G.get(u, v)
        Query[u].append((i, x, y, 1))
        Query[v].append((i, x, y, 1))
        Query[c].append((i, x, y, -2))

    ans = [0] * q
    S = [[0, 0] for _ in range(n)]

    def dfs(v, p=-1):
        for idx, color, mag, coef in Query[v]:
            x = G.dist[v]
            x -= S[color][1]
            x += mag * S[color][0]
            ans[idx] += x * coef
        for nv, color, d in to[v]:
            if nv == p: continue
            S[color][0] += 1
            S[color][1] += d
            dfs(nv, v)
            S[color][0] -= 1
            S[color][1] -= d
    dfs(0)
    print(*ans, sep="\n")

resolve()