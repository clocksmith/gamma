n = int(input())
while n > 0:
  l = [i for i in input()]
  l.sort()
  m = ''
  for s in l:
    m += s
  M = ''
  l.reverse()
  for t in l:
    M += t
  print(int(M)-int(m))
  n -= 1