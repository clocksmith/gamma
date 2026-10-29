"""Hack2Hire 677de134052a260e01657068 (Make Array Bitonic) over an INFERRED spec; qualification unknown."""


def solve(arr):
    n = len(arr)
    left = [0] * n
    right = [0] * n
    for c in range(n):
        left[c] = arr[c] if c == 0 else min(arr[c], left[c - 1] + 1)
    for c in range(n - 1, -1, -1):
        right[c] = arr[c] if c == n - 1 else min(arr[c], right[c + 1] + 1)
    best = 0
    for c in range(n):
        k = min(c + 1, n - c, left[c], right[c])
        if k > best:
            best = k
    return sum(arr) - best * best


class Solution:
    def minOperationsToBitonic(self, arr):
        return solve(arr)
