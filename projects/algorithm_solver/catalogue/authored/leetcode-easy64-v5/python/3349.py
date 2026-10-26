"""3349. Adjacent Increasing Subarrays Detection I (Easy).

Specification: https://leetcode.com/problems/adjacent-increasing-subarrays-detection-i/description/
"""


def solve(nums: list[int], k: int) -> bool:
    """O(n) time, O(1) auxiliary space; use one run split in two or adjacent increasing runs."""
    previous_run = 0
    current_run = 0
    for index in range(len(nums)):
        if index == 0 or nums[index] > nums[index - 1]:
            current_run += 1
        else:
            previous_run = current_run
            current_run = 1
        if current_run // 2 >= k or min(previous_run, current_run) >= k:
            return True
    return False


class Solution:
    def hasIncreasingSubarrays(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
