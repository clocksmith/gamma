# D - Fennec VS. Snuke
# https://atcoder.jp/contests/abc067/submissions/7707307
# https://atcoder.jp/contests/abc067/submissions/10252214
from collections import deque
n=int(input())
G=[[] for _ in range(n)]
for i in range(n-1):
    a,b=map(int,input().split())
    G[a-1].append(b-1)
    G[b-1].append(a-1)

dist_f=[-1]*n
dist_s=[-1]*n
dist_f[0]=0
dist_s[n-1]=0

q = deque()
q.append(0)
while q:
    x = q.popleft()
    for nx in G[x]:
        if dist_f[nx] == -1:
            q.append(nx)
            dist_f[nx]=dist_f[x]+1
 
q = deque()
q.append(n-1)
while q:
    x = q.popleft()
    for nx in G[x]:
        if dist_s[nx] == -1:
            q.append(nx)
            dist_s[nx]=dist_s[x]+1
f,s=0,0
for i in range(n):
    if dist_f[i]<=dist_s[i]:
        f+=1
    else:
        s+=1
if f>s:
    print('Fennec')
else:
    print('Snuke')