"""3819. Rotate Non Negative Elements."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> list[int]:
    """O(n) time and space; left rotation of nonnegative positions in a fresh result."""
    values = [value for value in nums if value >= 0]
    result = nums.copy()
    if not values:
        return result
    shift = k % len(values)
    cursor = 0
    for index, value in enumerate(nums):
        if value >= 0:
            result[index] = values[(cursor + shift) % len(values)]
            cursor += 1
    return result


class Solution:
    def rotateElements(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
