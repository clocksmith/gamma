"""2210. Count Hills and Valleys in an Array (Easy).

Specification: https://leetcode.com/problems/count-hills-and-valleys-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; count each plateau once without changing nums."""
    previous = nums[0]
    result = 0
    for index in range(1, len(nums) - 1):
        current, following = nums[index], nums[index + 1]
        if current == following:
            continue
        if ((current > previous and current > following) or
                (current < previous and current < following)):
            result += 1
        previous = current
    return result


class Solution:
    def countHillValley(self, nums: list[int]) -> int:
        return solve(nums)
