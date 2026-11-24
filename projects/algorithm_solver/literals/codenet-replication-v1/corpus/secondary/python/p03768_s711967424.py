import sys
from collections import defaultdict as dd
input = sys.stdin.readline
N, M = map(int, input().split())
e = dd(list)

for _ in range(M):
  u, v = map(int, input().split())
  e[u].append(v)
  e[v].append(u)
mxd = 0
res = [[-1] * 11 for _ in range(N + 1)]
Q = int(input())
qd = [0] * Q
qc = [0] * Q
for i in range(Q):
  v, d, c = map(int, input().split())
  qd[i] = d
  qc[i] = c
  res[v][d] = i
  mxd = max(mxd, d)
#print(qc)

#print(mxd)
for t in range(mxd):
  tres = [x[: ] for x in res]
  for x in range(1, N + 1):
    for y in e[x]:
      for i in range(t + 1, 11):
        res[y][i] = max(res[y][i], tres[x][i])

#print(res)
for r in res[1: ]:
  x = -1
  for i in range(11):
    if r[i] != -1: x = max(x, r[i])
  if x == -1: print(0)
  else: print(qc[x])