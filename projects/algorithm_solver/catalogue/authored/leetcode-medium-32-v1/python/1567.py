"""1567. Maximum Length of Subarray With Positive Product: track positive and negative product suffix lengths."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    positive = negative = best = 0
    for value in nums:
        if value > 0:
            positive += 1
            negative = negative + 1 if negative else 0
        elif value < 0:
            positive, negative = (negative + 1 if negative else 0), positive + 1
        else:
            positive = negative = 0
        best = max(best, positive)
    return best


class Solution:
    def getMaxLen(self, nums: list[int]) -> int:
        return solve(nums)
