class UnionFind():
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] == x:
            return x
        else:
            self.parent[x] = self.find(self.parent[x])
            return self.parent[x]

    def unite(self, x, y):
        x, y = self.find(x), self.find(y)

        if x == y:
            return

        if self.rank[x] < self.rank[y]:
            self.parent[x] = y
        else:
            self.parent[y] = x
            if self.rank[x] == self.rank[y]:
                self.rank[x] += 1

    def same(self, x, y):
        return self.find(x) == self.find(y)


while True:
    n, m = (int(s) for s in input().split())
    if not n:
        break

    result = 0
    bridges = sorted(
        (tuple(int(s) for s in input().split()) for i in range(m)),
        key=lambda x: x[2])
    tree = UnionFind(n)

    for a, b, cost in bridges:
        if not tree.same(a, b):
            result += cost
            tree.unite(a, b)
    print(result)