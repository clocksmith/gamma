n = int(input())
w = list(map(int, input().split()))
s2 = ans = sum(w)
s1 = 0
for i in range(n-1):
  s2 -= w[i]
  s1 += w[i]
  if ans < abs(s2-s1):
    break
  else:
    ans = abs(s2-s1)

print(ans)