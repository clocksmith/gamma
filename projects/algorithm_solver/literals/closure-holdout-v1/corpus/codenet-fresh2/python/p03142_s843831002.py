#書き足された各辺 u→v は、
#ある頂点 uからその子孫であるような
#頂点vに向かって伸びています。
#bfsでよい
from sys import stdin
from collections import deque
input = stdin.readline
n,m = map(int, input().split( ))

E = [[] for _ in range(n)]

P = [-1]*n
deg = [0]*n
for i in range(n+m-1):
    ai,bi = map(int, input().split( ))
    ai-=1;bi-=1
    E[ai].append(bi)
    deg[bi]+=1
r = deg.index(0)

Q = deque()
Q.append(r)
P[r] = r

while Q:
    v = Q.popleft()
    for u in E[v]:
        if deg[u]==1:
            P[u]=v
            deg[u]-=1
            Q.append(u)
        else:
            deg[u]-=1


for i in range(n):
    if P[i]==i:
        print(0)
    else:
        print(P[i]+1)
