from collections import *
from itertools import *

N = int(input())

A = map(int, input().split())
SA = SB = 0
ABI = sorted(((b:=max(N-i, i-1)*a, SA:=SA+a, SB:=SB+b) and (a, b, i) for i, a in enumerate(A, 1)), reverse=True)

prev = [0]
prev_max = 0
for k, (a, b, i) in enumerate(ABI):
  curr = [0]*(k+2)
  for l in range(k+1):
    r = k-l
    if prev[l] + SB - min(l,r)*SA < prev_max:
      continue
    curr[l] = max(curr[l], prev[l]+abs(N-i-r)*a)
    curr[l+1] = prev[l]+abs(i-l-1)*a
  SA -= a
  SB -= b
  prev = curr
  prev_max = max(prev)

print(prev_max)
