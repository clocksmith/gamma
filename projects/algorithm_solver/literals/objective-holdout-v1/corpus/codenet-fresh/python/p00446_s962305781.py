while True:
  n = int(input())
  if not n: break
  lst = [0 for i in range(n * 2)]
  for i in range(n):
    lst[int(input()) - 1] = 1
  T = [i for i in range(n * 2) if lst[i]]
  H = [i for i in range(n * 2) if not lst[i]]
  f = -1
  t = 0
  while T and H:
    if not t:
      for i in range(len(T)):
        if T[i] >= f:
          f = T.pop(i)
          t = 1
          break
      else:
        t = 1
        f = -1
    elif t:
      for i in range(len(H)):
        if H[i] >= f:
          f = H.pop(i)
          t = 0
          break
      else:
        t = 0
        f = -1
  print(len(H))
  print(len(T))



