from math import sqrt, pow
from operator import sub


def sub_(t):
    return abs(sub(*t))


n = input()
x = list(map(float, input().split()))
y = list(map(float, input().split()))

print(sum(map(sub_, zip(x, y))))
print(sqrt(sum(map(lambda t: sub_(t) ** 2, zip(x, y)))))
print(pow(sum(map(lambda t: sub_(t) ** 3, zip(x, y))), 1/3))
print(max(map(sub_, zip(x, y))))
