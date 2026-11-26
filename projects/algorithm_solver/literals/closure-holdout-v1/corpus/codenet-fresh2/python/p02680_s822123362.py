import sys
from collections import defaultdict

input = sys.stdin.readline
n, m = map(int, input().split())

xx = set([0]); yy = set([0]);
aa = []; bb = []; cc = []; dd = []; ee = []; ff = []; 
for _ in range(n):
    a, b, c = map(int, input().split())
    xx.add(a)
    xx.add(b)
    yy.add(c)
    aa.append(a); bb.append(b); cc.append(c); 
for _ in range(m):
    d, e, f = map(int, input().split())
    xx.add(d)
    yy.add(e)
    yy.add(f)
    dd.append(d); ee.append(e); ff.append(f); 
xx = sorted(list(xx))
yy = sorted(list(yy))
xp = defaultdict(int)
yp = defaultdict(int)

for i, v in enumerate(xx):
    xp[v] = i
for i, v in enumerate(yy):
    yp[v] = i

h = len(xx) - 1
w = len(yy) - 1
lx = [[0 for _ in range(w + 1)] for _ in range(h + 1)]
ly = [[0 for _ in range(w + 1)] for _ in range(h + 1)]

for i in range(n):
    a, b, c = aa[i], bb[i], cc[i]
    for x in range(xp[a], xp[b]):
        lx[x][yp[c]] = 1

for i in range(m):
    d, e, f = dd[i], ee[i], ff[i]
    for y in range(yp[e], yp[f]):
        ly[xp[d]][y] = 1

visited = [[False for _ in range(w)] for _ in range(h)]
sx, sy = min(xp[0], h - 1), min(yp[0], w - 1)
visited[sx][sy] = True
q = [(sx, sy)]
ans = 0

while q:
    x, y = q.pop()
    ans += (xx[x + 1] - xx[x]) * (yy[y + 1] - yy[y])
    if ly[x][y] == 0:
        if x == 0:
            print('INF'); exit();
        if not visited[x - 1][y]:
            visited[x - 1][y] = True
            q.append((x - 1, y))
    if lx[x][y] == 0:
        if y == 0:
            print('INF'); exit();
        if not visited[x][y - 1]:
            visited[x][y - 1] = True
            q.append((x, y - 1))
    if ly[x + 1][y] == 0:
        if x == h - 1:
            print('INF'); exit();
        if not visited[x + 1][y]:
            visited[x + 1][y] = True
            q.append((x + 1, y))
    if lx[x][y + 1] == 0:
        if y == w - 1:
            print('INF'); exit();
        if not visited[x][y + 1]:
            visited[x][y + 1] = True
            q.append((x, y + 1))

print(ans)
