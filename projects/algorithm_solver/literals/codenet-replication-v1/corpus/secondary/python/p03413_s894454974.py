from itertools import accumulate
n = int(input())
a = list(map(int,input().split()))
x = a[::2]
y = a[1::2]
lx = len(x)
ly = len(y)
sumx = sum([max(x[i],0) for i in range(lx)])
sumy = sum([max(y[i],0) for i in range(ly)])
ansls = []
if sumx >= sumy:
  ans = sumx
  flg = 0
else:
  ans = sumy
  flg = 1
if sumx == sumy == 0:
  ans = max(a)
  t = a.index(max(a))
  print(ans)
  print(n-1)
  for i in range(n,t+1,-1):
    print(i)
  for i in range(t):
    print(1)
  exit()
if flg:
  x = y
  lx = ly
  ansls.append(1)
  n -= 1
ls = [0]
fp = -1
fptmp = 0
for i in range(lx):
  if x[i] >= 0:
    ls.append(1)
    if fp == -1:
      fp = fptmp
  else:
    ls.append(-1)
    fptmp += 1
pnt = (n+1)//2*2-1
if pnt < n:
  ansls.append(n)
flgb = 0
while pnt > 0:
  px = (pnt+1)//2
  if not flgb and ls[px] < 0:
    ansls.append(pnt)
    ansls.append(pnt-1)
    ls.pop()
    pnt -= 2
  elif px <= fp:
    ansls.append(1)
    ansls.append(1)
    pnt -= 2
  elif ls[px] > 0:
    flgb = 1
    if px-1 <= fp:
      pnt -= 2
    elif ls[px-1] < 0:
      ansls.append(pnt-2)
      ls.pop()
      ls.pop()
      ls.append(1)
      pnt -= 2
    else:
      ansls.append(pnt-1)
      ls.pop()
      pnt -= 2
print(ans)
print(len(ansls))
print(*ansls,sep="\n")