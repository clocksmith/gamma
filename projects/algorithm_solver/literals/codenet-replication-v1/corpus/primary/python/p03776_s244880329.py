N, A, B = map(int, input().split())
X = list(map(int, input().split()))
X.sort(reverse=True)
M = sum(X[i] for i in range(A)) / A
print(M)
cntl, cntr = 0, 0
if X[A-1] == X[N-1]:
  cntr = N - A
else:
  cntr = A-1
  while X[A-1] == X[cntr]:
    cntr += 1
  cntr -= A
if X[0] == X[A-1]:
  cntl = A
else:
  cntl = A-1
  while X[A-1] == X[cntl]:
    cntl -= 1
  cntl = A - 1 - cntl
F = 0
c = cntl + cntr
if cntl == A:
  t = 1
  for m in range(A):
    t *= c - m
    t //= m + 1
  for m in range(A, min(B, c)+1):
    F += t
    t *= c - m
    t //= m + 1
  print(F)
else:
  # calc comb(cntl + cntr, cntl)
  t = 1
  for m in range(cntl):
    t *= c - m
    t //= m + 1
  F = t
  print(F)