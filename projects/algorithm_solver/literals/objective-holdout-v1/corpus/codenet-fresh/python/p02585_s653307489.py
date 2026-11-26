N,K = map(int,input().split())
P = list(map(int,input().split()))
for i in range(N):
  P[i]-=1
#print(P)
C = list(map(int,input().split()))
Flag = True
for c in C:
  if c >= 0:
    Flag = False
    break
if Flag:
  print(max(C))
  exit()
L = []
for i in range(N):
  visited = set([])
  now = i
  temp = []
  while now not in visited:
    nxt = P[now]
    visited.add(now)
    temp.append(C[nxt])
    now = nxt
  L.append(temp)
#print(L)
ans = 0
S = []
for X in L:
  start = [0]
  for i in range(len(X)):
    temp = start[-1]+X[i]
    start.append(temp)
  S.append(start)
#print(S)
for X,SS in zip(L,S):
  n = len(X)
  cycle_sum = SS[-1]
  if K <= n:
    kouho = max(SS[:K+1])
  elif cycle_sum < 0:
    kouho = max(SS)
  else:
    amari = K%n
    loop = K//n
    first = 0 #余りよりも後で最大
    second = 0 #余りよりも前で最大
    first = (loop-1)*cycle_sum + max(SS)
    second = loop*cycle_sum + max(SS[:amari+1])
    kouho = max(first,second)
  ans = max(ans,kouho)
print(ans)
  
    
  
