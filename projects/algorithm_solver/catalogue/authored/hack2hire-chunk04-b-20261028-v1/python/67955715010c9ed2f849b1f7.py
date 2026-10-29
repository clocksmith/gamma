"""Hack2Hire 67955715010c9ed2f849b1f7 (Binary Search Variation) over an INFERRED spec; qualification unknown."""


def solve(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(arr) and arr[lo] == target:
        return lo
    return lo - 1


class Solution:
    def binarySearch(self, arr, target):
        return solve(arr, target)
