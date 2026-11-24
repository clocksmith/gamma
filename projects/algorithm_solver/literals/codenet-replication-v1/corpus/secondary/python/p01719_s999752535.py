#!/usr/bin/env python
# -*- coding: utf-8 -*-

n,d,x = map(int,input().split())
weights = []
for i in range(d):
    weights.append(list(map(int,input().split())))

prices = []
for i in range(d-1):
    prices.append([weights[i+1][j] - weights[i][j] for j in range(n)])

bag = x
for i in range(d-1):
    dp = [False for i in range(bag+1)]
    dp[0] = 0
    for j in range(n):
        for k in range(bag):
            if weights[i][j] + k < bag+1 and dp[k] is not False:
                dp[k+weights[i][j]] = max(dp[k+weights[i][j]],dp[k] + prices[i][j])

    bag += max(dp[:bag+1])

print(bag)