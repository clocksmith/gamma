"""3678. Smallest Absent Positive Greater Than Average (Easy).

Specification: https://leetcode.com/problems/smallest-absent-positive-greater-than-average/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time and space; use floor division, including negative sums."""
    present = set(nums)
    total = sum(nums)
    candidate = max(1, total // len(nums) + 1)
    while candidate in present:
        candidate += 1
    return candidate


class Solution:
    def smallestAbsent(self, nums: list[int]) -> int:
        return solve(nums)
