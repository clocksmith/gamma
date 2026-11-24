R, G, B, N = map(int, input().split())
r, g, b = sorted([R, G, B], reverse=True)
ans = 0
for i in range(int(N / r) + 1):
  for j in range(int((N - i * r) / g) + 1):
    if (N - i * r - j * g) % b == 0:
      ans += 1
print(ans)