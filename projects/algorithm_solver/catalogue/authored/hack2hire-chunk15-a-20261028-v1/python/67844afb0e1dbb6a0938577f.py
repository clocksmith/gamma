"""Hack2Hire 67844afb0e1dbb6a0938577f (Count Valid Binary Combinations) over an INFERRED spec; qualification unknown."""


def solve(arr, pattern):
    n, m = len(pattern), len(arr)
    zeros = [0] * (n + 1)
    for i, ch in enumerate(pattern):
        zeros[i + 1] = zeros[i] + (1 if ch == '0' else 0)
    ways = [[0] * (m + 1) for _ in range(n + 1)]
    ways[n][m] = 1
    for i in range(n - 1, -1, -1):
        for j in range(m, -1, -1):
            total = 0
            if pattern[i] != '1':
                total += ways[i + 1][j]
            if j < m:
                end = i + arr[j]
                if end <= n and zeros[end] == zeros[i]:
                    if end == n:
                        total += ways[n][j + 1]
                    elif pattern[end] != '1':
                        total += ways[end + 1][j + 1]
            ways[i][j] = total
    return ways[0][0]


class Solution:
    def countCombinations(self, arr, pattern):
        return solve(arr, pattern)
