class Union_Find():
    def __init__(self, N):
        self.N = N
        self.par = [n for n in range(N)]
        self.rank = [0] * N
        
    def root(self, x):
        if self.par[x] == x:
            return x
        else:
            return self.root(self.par[x])
    
    def same(self, x, y):
        if self.root(x) == self.root(y):
            return True
        else:
            return False
    
    def unite(self, x, y):
        x = self.root(x)
        y = self.root(y)
        if (x==y): return
        if (self.rank[x] < self.rank[y]):
            self.par[x] = y
            self.rank[y] += self.rank[x] + 1
        else:
            self.par[y] = x
            self.rank[x] += self.rank[y] + 1

N, M = map(int, input().split())
UF = Union_Find(N)
for _ in range(M):
    a, b = map(int, input().split())
    a -= 1
    b -= 1
    UF.unite(a, b)
ans = -1
for n in range(N):
        ans = max(ans, UF.rank[n])
print(ans+1)