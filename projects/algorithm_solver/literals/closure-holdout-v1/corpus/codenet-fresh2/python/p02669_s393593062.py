#!/usr/bin python3
# -*- coding: utf-8 -*-

T = int(input())
from collections import deque
INF = 10**18

def transit(n, i, p):
    if p == 1:
        num = ((n+(i-1))//i)*i
        cos = d * (num - n)
        num //= i
        cos += ci[i]
    else:
        num = (n//i)*i
        cos = d * (n - num)
        num //= i
        cos += ci[i]
    return (num, cos)

for _ in range(T):
    N, a2, a3, a5, d = map(int, input().split())
    ci = {}
    ci[2]=a2
    ci[3]=a3
    ci[5]=a5
    dp = {}
    def cost(n):
        if n == 0:
            return 0
        if n == 1:
            return d
        if n in dp:
            return dp[n]
        ret = n * d
        for i in [2,3,5]:
            num, cos = transit(n, i, 1)
            ret = min(ret, cos + cost(num))
            num, cos = transit(n, i, -1)
            ret = min(ret, cos + cost(num))
        dp[n] = ret
        return ret
    print(cost(N))
