"""3718. Smallest Missing Multiple of K (Easy).

Specification: https://leetcode.com/problems/smallest-missing-multiple-of-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and space; at most n present multiples can be skipped."""
    present = set(nums)
    candidate = k
    while candidate in present:
        candidate += k
    return candidate


class Solution:
    def missingMultiple(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
