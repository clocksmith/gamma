h, a, b = map(int, input().split())
ans = 0
for i in range(a, b + 1):
  if h % i == 0:
    ans += 1
print(ans)
