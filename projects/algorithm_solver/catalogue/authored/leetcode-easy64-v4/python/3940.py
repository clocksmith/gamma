"""3940. Limit Occurrences in Sorted Array (Easy).

Specification: https://leetcode.com/problems/limit-occurrences-in-sorted-array/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time, O(1) auxiliary space beyond the output; return a new array and preserve nums."""
    result = []
    for value in nums:
        if len(result) < k or value != result[-k]:
            result.append(value)
    return result


class Solution:
    def limitOccurrences(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
