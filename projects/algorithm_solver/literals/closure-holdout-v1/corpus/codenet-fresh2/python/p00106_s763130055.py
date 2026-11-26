INF = 10 ** 20

def solve(n):
  ans = INF
  for i in range(n // 500 + 1):
    for j in range((n - 500 * i) // 300 + 1):
      if not (n - 500 * i - 300 * j) % 200:
        a = (n - 500 * i - 300 * j) // 200
        va = a // 5 * 1900 * 0.8  + a % 5 * 380
        vb = j // 4 * 2200 * 0.85 + j % 4 * 550
        vc = i // 3 * 2550 * 0.88 + i % 3 * 850
        ans = min(ans, va + vb + vc)
  print(int(ans))

while True:
  n = int(input())
  if not n:
    break
  solve(n)
