"""2357. Make Array Zero by Subtracting Equal Amounts (Easy).

Specification: https://leetcode.com/problems/make-array-zero-by-subtracting-equal-amounts/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(u) space; each distinct positive level requires one subtraction."""
    return len({value for value in nums if value > 0})


class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        return solve(nums)
