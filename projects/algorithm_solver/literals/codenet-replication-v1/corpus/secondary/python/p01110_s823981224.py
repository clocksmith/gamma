class Paper:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.table = [[1] * n for _ in range(m)]

    def __str__(self):
        return str(self.table)

    def thickness(self, x, y):
        return self.table[y][x]

    def fold(self, d, c):
        if d == 1:
            return self.foldl(c)
        else:
            return self.foldb(c)

    def foldl(self, c):
        nn = max(c, self.n - c)
        tbl = [[0] * nn for _ in range(self.m)]
        for y in range(self.m):
            for x in range(c):
                tbl[y][x] += self.table[y][c - x - 1]
            for x in range(self.n - c):
                tbl[y][x] += self.table[y][c + x]
        self.n = nn
        self.table = tbl

    def foldb(self, c):
        mm = max(c, self.m - c)
        tbl = [[0] * self.n for _ in range(mm)]
        for x in range(self.n):
            for y in range(c):
                tbl[y][x] += self.table[c - y - 1][x]
            for y in range(self.m - c):
                tbl[y][x] += self.table[c + y][x]
        self.m = mm
        self.table = tbl

while True:
    n, m, t, p = map(int, input().split())
    if n == m == t == p == 0:
        break

    paper = Paper(n, m)
    for i in range(t):
        d, c = map(int, input().split())
        paper.fold(d, c)
    for i in range(p):
        x, y = map(int, input().split())
        print(paper.thickness(x, y))
