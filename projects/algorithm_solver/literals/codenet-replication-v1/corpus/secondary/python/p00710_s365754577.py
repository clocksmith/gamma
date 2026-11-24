import sys

while 1:
    n, r = map(int, sys.stdin.readline().split())

    if (n, r) == (0, 0):
        break

    yama = [int(n - i) for i in range(n)]

    for lp in range(r):
        p, c = map(int, sys.stdin.readline().split())
        p -= 1
        yama = yama[p:p + c] + yama[:p] + yama[p + c:]

    print(yama[0])