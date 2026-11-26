class BIT:
  def __init__(self, n):
    self.n = n
    self.data = [0]*(n+1)
    self.el = [0]*(n+1)
  def sum(self, i):
    s = 0
    while i > 0:
      s += self.data[i]
      i -= i & -i
    return s
  def add(self, i, x):
    # assert i > 0
    self.el[i] += x
    while i <= self.n:
      self.data[i] += x
      i += i & -i
  def get(self, i, j=None):
    if j is None:
      return self.el[i]
    return self.sum(j) - self.sum(i)


n=int(input())
xy=[list(map(int,input().split())) for _ in range(n)]
xy=[(i,x,y)for i,(x,y) in enumerate(xy)]
xy.sort(key=lambda x:x[1])
g=[set() for _ in range(n)]
bit=BIT(n)
work=[-1]*(n+1)
for i,x,y in xy:
  k=bit.sum(y)
  l,r=1,y+1
  c=y+1
  for j in range(k,0,-1):
    l,r=1,c
    while r-l>1:
      c=(r+l)//2
      if bit.sum(c)>=j:
        l,r=l,c
      else:
        l,r=c,r
    c=l if bit.sum(l)==j else r
    idx=work[c]
    g[idx].add(i)
    g[i].add(idx)
    if j>1:bit.add(c,-1)
  if k==0:bit.add(y,1)
  if k==0:work[y]=i

ans=[0]*n
mi=set(range(n))
while mi:
  s=mi.pop()
  grp={s}
  todo=[s]
  cnt=1
  while todo:
    v=todo.pop()
    for nv in g[v]:
      if nv not in grp:
        todo.append(nv)
        grp.add(nv)
        mi.discard(nv)
        cnt+=1
  for id in grp:
    ans[id]=cnt
print(*ans,sep='\n')
#print(g)
#print(bit.sum(1))
