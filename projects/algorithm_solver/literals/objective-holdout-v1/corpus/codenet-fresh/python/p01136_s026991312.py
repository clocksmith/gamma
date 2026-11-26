#!/usr/bin/env python
# -*- coding: utf-8 -*-

while True:
    N = int(input())
    if N == 0:
        break
    dates = [[] for i in range(31)]
    meets = [[] for i in range(N)]

    for i in range(N):
        D = list(map(int,input().split()))
        for d in D[1:]:
            dates[d].append(i)

    for i in range(31):
        hoge = []
        for p in dates[i]:
            hoge = set(hoge) | set(meets[p])
        for p in dates[i]:
            meets[p] = set(hoge) | set(dates[i])
            if len(meets[p]) == N:
                break
        else:
            continue
        break
    else:
        print(-1)
        continue
    print(i)