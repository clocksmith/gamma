# coding: utf-8


K, T = map(int, input().split(" "))
a = list(map(int, input().split(" ")))
m = max(a)
s = sum(a) - m
if m - s < 2:
    print(0)
else:
    print(m - s - 1)
