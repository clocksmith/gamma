"""659. Split Array into Consecutive Subsequences (Medium).

Specification: https://leetcode.com/problems/split-array-into-consecutive-subsequences/description/
"""


def solve(nums: list[int]) -> bool:
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    tails = {}
    for value in nums:
        if counts.get(value, 0) == 0:
            continue
        counts[value] -= 1
        if tails.get(value - 1, 0) > 0:
            tails[value - 1] -= 1
            tails[value] = tails.get(value, 0) + 1
        elif counts.get(value + 1, 0) > 0 and counts.get(value + 2, 0) > 0:
            counts[value + 1] -= 1
            counts[value + 2] -= 1
            tails[value + 2] = tails.get(value + 2, 0) + 1
        else:
            return False
    return True


class Solution:
    def isPossible(self, nums: list[int]) -> bool:
        return solve(nums)
