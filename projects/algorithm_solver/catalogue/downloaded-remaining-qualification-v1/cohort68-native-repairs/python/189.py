"""189. Rotate Array (Medium).

Specification: https://leetcode.com/problems/rotate-array/description/
"""


def solve(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    if n == 0:
        return []
    steps = k % n
    return nums[n - steps:] + nums[:n - steps]


class Solution:
    def rotate(self, nums: list[int], k: int) -> None:
        size = len(nums)
        steps = k % size
        if not steps:
            return
        def reverse(left, right):
            while left < right:
                nums[left], nums[right] = nums[right], nums[left]
                left += 1
                right -= 1
        reverse(0, size - 1)
        reverse(0, steps - 1)
        reverse(steps, size - 1)
