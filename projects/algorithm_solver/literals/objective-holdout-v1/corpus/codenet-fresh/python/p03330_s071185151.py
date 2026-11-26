import sys
import itertools
import numpy as np
MOD = 3
INF = 1000000000


def input():
    return sys.stdin.readline().rstrip()


def main():
    n, c = [int(e) for e in input().split()]
    dMat = [[int(e) for e in input().split()] for _ in range(c)]
    cMat = [[int(e) for e in input().split()] for _ in range(n)]

    cost = [[0 for _ in range(c)] for _ in range(MOD)]
    for hi in range(n):
        for wi in range(n):
            cMod = ((hi + 1) + (wi + 1)) % MOD
            for ci in range(c):
                cost[cMod][ci] += dMat[cMat[hi][wi] - 1][ci]

    ans = INF
    for perm in itertools.permutations(range(c), MOD):
        costSum = 0
        for di in range(MOD):
            costSum += cost[di][perm[di]]
        ans = min(ans, costSum)
    print(ans)


main()
