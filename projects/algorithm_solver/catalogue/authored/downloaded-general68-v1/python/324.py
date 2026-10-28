"""324. Wiggle Sort II (Medium).

Specification: https://leetcode.com/problems/wiggle-sort-ii/description/
"""


def solve(nums: list[int]) -> list[int]:
    ordered = sorted(nums)
    n = len(ordered)
    small = ordered[:(n + 1) // 2][::-1]
    large = ordered[(n + 1) // 2:][::-1]
    result = []
    for i in range(n):
        result.append(small[i // 2] if i % 2 == 0 else large[i // 2])
    return result


class Solution:
    def wiggleSort(self, nums: list[int]) -> list[int]:
        return solve(nums)
