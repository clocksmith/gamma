from collections import defaultdict

N, M = map(int, input().split())
iPY = []
D = defaultdict(list)
E = defaultdict(int)

for i in range(M):
  P, Y = map(int, input().split())
  iPY.append((i, P, Y))

iPY.sort(key = lambda x: x[2])

for i, P, Y in iPY:
  D[P].append(Y)

for P, Ys in D.items():
  for i, Y in enumerate(Ys):
    E[Y] = "000000"+str(i+1)

iPY.sort()

for i, P, Y in iPY:
  U = "000000"+str(P)
  L = E[Y]
  print(U[-6:]+L[-6:])