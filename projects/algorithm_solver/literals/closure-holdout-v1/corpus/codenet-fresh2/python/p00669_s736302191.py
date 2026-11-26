from functools import reduce
from collections import Counter
while True:
  n, k = map(int, input().split())
  if n == 0:
    break
  clst = [int(input()) for _ in range(n)]
  acc = reduce(lambda x, y:x* y, clst[:k])
  scores = [acc]
  for i in range(n - k):
    acc = acc // clst[i] * clst[i + k]
    scores.append(acc)
  
  score = 0
  for i in range(n):
    for j in range(i + 1, n):
      p = clst[i]
      q = clst[j]
      for x in range(i - k + 1, i + 1):
        if abs(j - x) >= k and 0 <= x <= n - k:
          score = max(score, scores[x] // p * q)
      for x in range(j - k + 1, j + 1):
        if abs(x - i) >= k and 0 <= x <= n - k:
          score = max(score, scores[x] // q * p)
  if score < max(scores):
    print("NO GAME")
  else:
    print(score - max(scores))
