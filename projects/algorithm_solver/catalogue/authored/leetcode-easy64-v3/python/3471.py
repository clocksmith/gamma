"""3471. Find the Largest Almost Missing Integer (Easy).

Specification: https://leetcode.com/problems/find-the-largest-almost-missing-integer/description/
"""


def solve(nums: list[int], k: int) -> int:
    """O(n * k) expected time, O(n) space; count windows containing each value, not occurrences."""
    windows = {}
    for start in range(len(nums) - k + 1):
        present = set()
        for index in range(start, start + k):
            present.add(nums[index])
        for value in present:
            windows[value] = windows.get(value, 0) + 1
    largest = -1
    for value, count in windows.items():
        if count == 1:
            largest = max(largest, value)
    return largest


class Solution:
    def largestInteger(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
