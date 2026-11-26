import sys
from collections import deque


class P(list):
    def __init__(self):
        list.__init__(self)
        self.space = None
        self.path = ""

    def __hash__(self):
        return hash(str(self[:]))


def is_target(p):
    return p[:] == ans[:]


N = 3
N2 = N*N
ans = [1, 2, 3, 4, 5, 6, 7, 8, 9]
# space index
si = 0

# move
dx = (-1, 0, 1, 0)
dy = (0, -1, 0, 1)
direction = ('u', 'l', 'd', 'r')


def bfs(p):
    Q = deque()
    Q.append(p)
    V = set()
    V.add(p)

    while Q:
        u = Q.popleft()
        if u == ans:
            return u.path
        sx = u.space // N
        sy = u.space % N
        for i in range(4):
            tx = sx + dx[i]
            ty = sy + dy[i]
            if tx < 0 or ty < 0 or tx >= N or ty >= N:
                continue
            v = P()
            v[:] = u[:]
            v.path = u.path
            c = int(tx*N+ty)
            v[u.space] = v[c]
            v[c] = 9
            v.space = c
            if v not in V:
                V.add(v)
                v.path += direction[i]
                Q.append(v)


p = P()
for i in range(N):
    line = sys.stdin.readline()
    a, b, c = map(int, line.split())
    p.append(a)
    p.append(b)
    p.append(c)
for i in range(N2):
    if p[i] == 0:
        p[i] = 9
        p.space = i

re = bfs(p)
print(len(re))

