"""3396. Minimum Number of Operations to Make Elements in Array Distinct (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-operations-to-make-elements-in-array-distinct/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) expected time, O(n) space; find the longest distinct suffix without mutation."""
    seen = set()
    for index in range(len(nums) - 1, -1, -1):
        if nums[index] in seen:
            return index // 3 + 1
        seen.add(nums[index])
    return 0


class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        return solve(nums)
