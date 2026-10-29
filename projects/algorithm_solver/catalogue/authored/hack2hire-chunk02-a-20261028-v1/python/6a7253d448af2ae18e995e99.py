"""Hack2Hire 6a7253d448af2ae18e995e99 (Minimum Nondecreasing Increment); INFERRED spec; qualification unknown."""


def solve(arr):
    n = len(arr)
    x, previous_forced = 0, -2
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            if previous_forced == i: return -1  # i and i+1 would both need to be chosen
            previous_forced = i + 1
            x = max(x, arr[i] - arr[i + 1])
    for i in range(n - 1):
        if arr[i] > arr[i + 1] and i + 2 < n and arr[i + 1] + x > arr[i + 2]: return -1
    return x


class Solution:
    def minNondecreasingIncrement(self, arr):
        return solve(arr)
