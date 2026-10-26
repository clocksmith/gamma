"""3095. Shortest Subarray With OR at Least K I (Easy).

Specification: https://leetcode.com/problems/shortest-subarray-with-or-at-least-k-i/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n^2) time, O(1) space; declared values fit six bits, so bitwise OR is exact."""
    shortest = len(nums) + 1
    for left in range(len(nums)):
        combined = 0
        for right in range(left, len(nums)):
            combined |= nums[right]
            if combined >= k:
                shortest = min(shortest, right - left + 1)
                break
    return shortest if shortest <= len(nums) else -1


class Solution:
    def minimumSubarrayLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
