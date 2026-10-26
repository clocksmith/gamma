"""2874. Maximum Value of an Ordered Triplet II: carry the best earlier value and earlier ordered difference before scoring each endpoint."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space on the positive integer domain; inputs are read-only."""
    largest = nums[0]
    difference = 0
    best = 0
    for index in range(1, len(nums)):
        value = nums[index]
        best = max(best, difference * value)
        difference = max(difference, largest - value)
        largest = max(largest, value)
    return best


class Solution:
    def maximumTripletValue(self, nums: list[int]) -> int:
        return solve(nums)
