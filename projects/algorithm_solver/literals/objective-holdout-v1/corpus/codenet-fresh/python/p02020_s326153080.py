n = int(input())
a = list(map(int, input().split()))

r = sum(a)
if r % 2 == 0:
  print(r // 2)
else:
  a.sort()
  for j in a:
    if (r - j) % 2 == 0:
      print((r-j) // 2)
      break
