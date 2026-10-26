"""3277. Maximum XOR Score Subarray Queries: interval XOR recurrence with a packed range-maximum table."""

from array import array


def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    """O(n^2 + q) time and O(n^2 + q) space. Inputs are preserved."""
    n = len(nums)
    best = [None] * n
    below_score = array('I', [0]) * n
    for left in range(n - 1, -1, -1):
        score = array('I', [0]) * n
        row = array('I', [0]) * n
        score[left] = row[left] = nums[left]
        for right in range(left + 1, n):
            score[right] = score[right - 1] ^ below_score[right]
            row[right] = max(score[right], row[right - 1], best[left + 1][right])
        best[left] = row
        below_score = score
    return [best[left][right] for left, right in queries]


class Solution:
    def maximumSubarrayXor(self, nums: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
