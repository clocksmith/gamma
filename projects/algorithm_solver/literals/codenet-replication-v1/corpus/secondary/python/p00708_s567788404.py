class UnionFind:
    def __init__(self, n):
        self.par = [i for i in range(n)]
        self.rank = [0] * n
        self.size = [1] * n

    def find(self, x):
        if self.par[x] == x:
            return x
        else:
            self.par[x] = self.find(self.par[x])
            return self.par[x]

    def unite(self, x, y):
        x = self.find(x)
        y = self.find(y)
        if x == y:
            return
        
        if self.rank[x] < self.rank[y]:
            self.par[x] = y
            self.size[y] += self.size[x]
        else:
            self.par[y] = x
            self.size[x] += self.size[y]
            if self.rank[x] == self.rank[y]:
                self.rank[x] += 1
    
    def same(self, x, y):
        if self.find(x) == self.find(y):
            return True
        else:
            return False


def kruskal(n, edges):
    uf = UnionFind(n)
    edges.sort()
    res = 0
    for c, s, t in edges:
        if not uf.same(s, t):
            res += c
            uf.unite(s, t)
    return res

while True:
    n = int(input())
    if n == 0: break

    x = [0] * n
    y = [0] * n
    z = [0] * n
    r = [0] * n
    for i in range(n):
        x[i], y[i], z[i], r[i] = map(float, input().split())
    
    edges = []
    for i in range(n):
        for j in range(n):
            if i == j: continue
            c = max(((x[i]-x[j])**2 + (y[i]-y[j])**2 + (z[i]-z[j])**2)**(1/2) - (r[i]+r[j]), 0)
            edges.append((c, i, j))
    
    print("{:.3f}".format(kruskal(n, edges)))

