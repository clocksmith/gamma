"""2256. Minimum Average Difference: compare prefix and suffix averages with earliest-index ties."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    total = sum(nums)
    prefix = 0
    best_difference = float("inf")
    answer = 0
    for index, value in enumerate(nums):
        prefix += value
        left_average = prefix // (index + 1)
        remaining = len(nums) - index - 1
        right_average = (total - prefix) // remaining if remaining else 0
        difference = abs(left_average - right_average)
        if difference < best_difference:
            best_difference = difference
            answer = index
    return answer


class Solution:
    def minimumAverageDifference(self, nums: list[int]) -> int:
        return solve(nums)
