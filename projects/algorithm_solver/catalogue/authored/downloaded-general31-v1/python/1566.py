"""1566. Detect Pattern of Length M Repeated K or More Times (Easy).

Specification: https://leetcode.com/problems/detect-pattern-of-length-m-repeated-k-or-more-times/description/
"""


def solve(arr: list[int], m: int, k: int) -> bool:
    for start in range(len(arr) - m * k + 1):
        ok = True
        for offset in range(m * k):
            if arr[start + offset] != arr[start + (offset % m)]:
                ok = False
                break
        if ok:
            return True
    return False


class Solution:
    def containsPattern(self, arr: list[int], m: int, k: int) -> bool:
        return solve(arr, m, k)
