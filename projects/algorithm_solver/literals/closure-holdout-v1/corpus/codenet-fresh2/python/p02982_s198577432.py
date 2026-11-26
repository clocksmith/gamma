# -*- coding:utf-8 -*-
import math

N, D = map(int, input().split())
X = [list(map(int, input().split())) for _ in range(N)]

counter = 0
for i in range(N - 1):
    for j in range(i + 1, N):
        e = 0
        for xi, xj in zip(X[i], X[j]):
            e += (xj - xi)**2
        e = e**0.5
        counter += 1 if float.is_integer(e) else 0

print(counter)