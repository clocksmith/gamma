import sys
sys.setrecursionlimit(200000000)

A, B = map(int, input().split())

def extgcd(a, b, x, y):
    d = a
    if b != 0:
        y, x = extgcd(b, a % b, y, x)
        y -= (a // b) * x
        return x, y
    else:
        return (1, 0)

x, y = extgcd(A, B, 0, 0)
print("{} {}".format(x, y))

