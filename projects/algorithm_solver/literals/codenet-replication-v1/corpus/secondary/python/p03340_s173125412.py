# -*- coding: utf-8 -*-
N = int(input())
An = list(map(int, input().split()))

# 尺取
ans = 0
l = 0
r = 0
Asum = An[0]
Axor = An[0]
while l < N and r < N:
    if Asum == Axor:
        ans += r-l+1
        r += 1
        if r < N:
            Asum += An[r]
            Axor ^= An[r]
    else:
        if l < N:
            Asum -= An[l]
            Axor ^= An[l]
        l += 1

print(ans)
