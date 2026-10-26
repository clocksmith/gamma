"""2970. Count the Number of Incremovable Subarrays I (Easy).

Specification: https://leetcode.com/problems/count-the-number-of-incremovable-subarrays-i/description/
"""


def solve(nums: list[int]) -> int:
    """O(n^2) time, O(n) space; prefix/suffix validity avoids copying each removal."""
    count = len(nums)
    prefix = [True] * count
    suffix = [True] * count
    for index in range(1, count):
        prefix[index] = prefix[index - 1] and nums[index - 1] < nums[index]
    for index in range(count - 2, -1, -1):
        suffix[index] = suffix[index + 1] and nums[index] < nums[index + 1]
    result = 0
    for left in range(count):
        if left > 0 and not prefix[left - 1]:
            continue
        for right in range(left, count):
            if right + 1 < count and not suffix[right + 1]:
                continue
            if left > 0 and right + 1 < count and nums[left - 1] >= nums[right + 1]:
                continue
            result += 1
    return result


class Solution:
    def incremovableSubarrayCount(self, nums: list[int]) -> int:
        return solve(nums)
