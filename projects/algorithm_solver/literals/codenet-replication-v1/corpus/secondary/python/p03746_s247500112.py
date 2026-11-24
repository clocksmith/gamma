from collections import deque
n,m=map(int,input().split())
g=[[] for i in range(1+n)]
v=[0]*(1+n)
for i in range(m):
    a,b=map(int,input().split())
    g[a].append(b)
    g[b].append(a)
    if i==0:
        q=[a,b]
        v[a]=v[b]=1

p=[q[-1]]
path=[]
while p:
    cur=p.pop()
    path.append(cur)
    v[cur]=1
    flg=True
    for i in g[cur]:
        if v[i]==0:
            p.append(i)
            flg=False
    if flg:
        break
ans=path

p=[q[0]]
path=[]
while p:
    cur=p.pop()
    path.append(cur)
    v[cur]=1
    flg=True
    for i in g[cur]:
        if v[i]==0:
            p.append(i)
            flg=False
    if flg:
        break
ans=path[::-1]+ans
print(len(ans))
print(*ans)