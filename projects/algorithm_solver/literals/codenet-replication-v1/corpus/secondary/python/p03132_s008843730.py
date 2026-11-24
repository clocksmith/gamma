import sys
input = sys.stdin.readline
import numpy as np

N = int(input())
A = [int(input()) for _ in range(N)]

p1 = 0
p2 = 0
P1 = [0]
P2 = [0]
for a in A:
    if a == 0:
        p1 -= 2
        p2 += 1
    elif a % 2 == 0:
        p2 -= 1
    elif a % 2 == 1:
        p1 -= 1
        p2 += 1
    p1 += a
    P1.append(p1)
    P2.append(p2)

dp = [P1[N], P1[N]+P2[N], -P1[N], 0]

for i in reversed(range(N)):
    dp[0] = max(dp[0], P1[i])
    dp[1] = max(dp[1], P2[i]+dp[0])
    dp[2] = min(dp[2], P2[i]-dp[1])
    dp[3] = min(dp[3], P1[i]+dp[2])

print(dp[3]+sum(A))
