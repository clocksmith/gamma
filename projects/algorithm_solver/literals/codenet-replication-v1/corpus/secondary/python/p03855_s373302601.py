import sys
from collections import defaultdict
sys.setrecursionlimit(10**7)

class UnionFind():
    def __init__(self, N):
        self.N = N
        self.par = [n for n in range(N)]
        self.rank = [0 for _ in range(N)]

    def find(self, x):
        if self.par[x] == x:
            return x
        self.par[x] = self.find(self.par[x])
        return self.par[x]

    def union(self, x, y):
        x = self.find(self.par[x])
        y = self.find(self.par[y])
        if self.rank[x] < self.rank[y]:
            self.par[x] = y
        else:
            self.par[y] = x
            if self.rank[x] == self.rank[y]:
                self.rank[x] += 1

    def isSame(self, x, y):
        return self.par[x] == self.par[y]

    def refresh(self):
        for p in range(N):
            self.find(p)

N, K, L = [int(x) for x in input().strip().split()]
road = UnionFind(N)
train = UnionFind(N)

for ｋ in range(K):
    p, q = [int(x) - 1 for x in input().strip().split()]
    road.union(p, q)
for l in range(L):
    r, s = [int(x) - 1 for x in input().strip().split()]
    train.union(r, s)

d = defaultdict(int)
for n in range(N):
    r = road.find(n)
    t = train.find(n)
    d[(r, t)] += 1

for n in range(N):
    print(d[(road.par[n], train.par[n])], end=' ')