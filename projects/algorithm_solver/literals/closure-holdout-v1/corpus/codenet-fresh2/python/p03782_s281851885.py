# -*- coding: utf-8 -*-
def inpl(): return list(map(int, input().split()))
 
N, K = inpl()
A = sorted(inpl())
S = []
s = 0
for a in A:
    s += a
    S.append(s)

A = A[::-1]
DP = [True]+[False for _ in range(K-1)]

OK = [False for _ in range(N)]
 
for i, a in enumerate(A):
    DP1 = [False for _ in range(K)]
    if a >= K:
        OK[i] = True
        continue
    for j, d in enumerate(DP):
        if d:
            DP1[j] = True
            if j + a >= K:
                OK[i] = True
            else:
                DP1[j+a] = True
    DP = DP1

if sum(OK) == 0:
    print(N)
else:
    print(OK[::-1].index(True))