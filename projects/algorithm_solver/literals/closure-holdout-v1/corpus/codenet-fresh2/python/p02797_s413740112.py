n,k,s = map(int,input().split())
ans = []
for _ in range(k):
  ans.append(str(s))
for _ in range(n-k):
  if s != 10 ** 9:
    ans.append(str(s+1))
  else:
    ans.append(str(s-1))
print(' '.join(ans))