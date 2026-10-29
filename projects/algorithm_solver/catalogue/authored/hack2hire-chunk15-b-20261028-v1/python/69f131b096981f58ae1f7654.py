"""Hack2Hire 69f131b096981f58ae1f7654 (Find K Distinct Element Subarray) over an INFERRED spec; qualification unknown."""


def solve(arr, k):
    counts = {}
    distinct = 0
    best = -1
    left = 0
    for right, x in enumerate(arr):
        counts[x] = counts.get(x, 0) + 1
        if counts[x] == 1:
            distinct += 1
        while distinct >= k:
            length = right - left + 1
            if best < 0 or length < best:
                best = length
            y = arr[left]
            counts[y] -= 1
            if counts[y] == 0:
                distinct -= 1
            left += 1
    return best


class Solution:
    def shortestGoodSubarray(self, arr, k):
        return solve(arr, k)
