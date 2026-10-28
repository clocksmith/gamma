"""457. Circular Array Loop (Medium).

Specification: https://leetcode.com/problems/circular-array-loop/description/
"""


def _next_index(nums, index):
    n = len(nums)
    return (index + nums[index]) % n


def solve(nums: list[int]) -> bool:
    n = len(nums)
    for start in range(n):
        slow = start
        fast = start
        direction = nums[start] > 0
        while True:
            slow = _next_index(nums, slow)
            if (nums[slow] > 0) != direction:
                break
            fast = _next_index(nums, fast)
            if (nums[fast] > 0) != direction:
                break
            fast = _next_index(nums, fast)
            if (nums[fast] > 0) != direction:
                break
            if slow == fast:
                if slow == _next_index(nums, slow):
                    break
                return True
    return False


class Solution:
    def circularArrayLoop(self, nums: list[int]) -> bool:
        return solve(nums)
