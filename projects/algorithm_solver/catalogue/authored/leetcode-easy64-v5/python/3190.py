"""3190. Find Minimum Operations to Make All Elements Divisible by Three (Easy).

Specification: https://leetcode.com/problems/find-minimum-operations-to-make-all-elements-divisible-by-three/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) auxiliary space; each nonmultiple needs exactly one operation."""
    operations = 0
    for value in nums:
        if value % 3 != 0:
            operations += 1
    return operations


class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        return solve(nums)
