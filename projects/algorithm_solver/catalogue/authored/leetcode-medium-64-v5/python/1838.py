"""1838. Frequency of the Most Frequent Element: keep the largest sorted window that can be raised to its rightmost value."""


def solve(nums: list[int], k: int) -> int:
    """O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(nums)
    left = total = best = 0
    for right, value in enumerate(ordered):
        total += value
        while value * (right - left + 1) - total > k:
            total -= ordered[left]
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def maxFrequency(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
