"""Hack2Hire 69e93d83fbaf3da6418286c9 (Minimum Subarray with K Unique Integers) over an INFERRED spec; qualification unknown."""


def solve(arr, k):
    counts = {}
    best = -1
    left = 0
    for right, v in enumerate(arr):
        counts[v] = counts.get(v, 0) + 1
        while len(counts) >= k:
            length = right - left + 1
            if best == -1 or length < best:
                best = length
            w = arr[left]
            counts[w] -= 1
            if counts[w] == 0:
                del counts[w]
            left += 1
    return best


class Solution:
    def minLengthGoodSubarray(self, arr, k):
        return solve(arr, k)
