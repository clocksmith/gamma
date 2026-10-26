"""1671. Minimum Number of Removals to Make Mountain Array: strict LIS lengths in both directions; O(n log n) time and O(n) space."""

from bisect import bisect_left


def solve(nums: list[int]) -> int:
    def lengths(values):
        tails, answer = [], []
        for value in values:
            position = bisect_left(tails, value)
            if position == len(tails):
                tails.append(value)
            else:
                tails[position] = value
            answer.append(position + 1)
        return answer

    increasing = lengths(nums)
    decreasing = lengths(reversed(nums))[::-1]
    longest = max((left + right - 1 for left, right in zip(increasing, decreasing)
                   if left > 1 and right > 1), default=0)
    return len(nums) - longest


class Solution:
    def minimumMountainRemovals(self, nums: list[int]) -> int:
        return solve(nums)
