def coll(n):
  cnt = 0
  while n > 1:
    if n % 2:
      n = n * 3 + 1
      cnt += 1
    while n % 2 == 0:
      n = n // 2
      cnt += 1
  return cnt

while True:
  n = int(input())
  if n == 0:
    break
  print(coll(n))
