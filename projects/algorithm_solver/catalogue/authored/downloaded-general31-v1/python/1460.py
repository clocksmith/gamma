"""1460. Make Two Arrays Equal by Reversing Subarrays (Easy).

Specification: https://leetcode.com/problems/make-two-arrays-equal-by-reversing-subarrays/description/
"""


def solve(target: list[int], arr: list[int]) -> bool:
    return sorted(target) == sorted(arr)


class Solution:
    def canBeEqual(self, target: list[int], arr: list[int]) -> bool:
        return solve(target, arr)
