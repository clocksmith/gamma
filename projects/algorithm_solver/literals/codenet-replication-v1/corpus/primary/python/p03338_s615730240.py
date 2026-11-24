import collections

n = int(input())
s = input()
l1 = []
l2 = []
ans = 0
for i in range(1,n):
  l1 = set(list(s[0:i:]))
  l2 = set(list(s[i::]))
  ans = max(ans,len(l1&l2))
#  print(l1,l2,ans)
  
print(ans)