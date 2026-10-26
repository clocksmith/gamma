"""3432. Count Partitions with Even Sum Difference (Easy).

Specification: https://leetcode.com/problems/count-partitions-with-even-sum-difference/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; every partition difference has the parity of the total."""
    total = sum(nums)
    return len(nums) - 1 if total % 2 == 0 else 0


class Solution:
    def countPartitions(self, nums: list[int]) -> int:
        return solve(nums)
