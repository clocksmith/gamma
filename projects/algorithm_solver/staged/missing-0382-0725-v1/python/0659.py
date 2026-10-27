"""659. Split Array into Consecutive Subsequences."""

from collections import Counter

def solve(nums: list[int]) -> bool:
    counts = Counter(nums)
    tails = Counter()
    for value in nums:
        if counts[value] == 0:
            continue
        counts[value] -= 1
        if tails[value - 1]:
            tails[value - 1] -= 1
            tails[value] += 1
        elif counts[value + 1] and counts[value + 2]:
            counts[value + 1] -= 1
            counts[value + 2] -= 1
            tails[value + 2] += 1
        else:
            return False
    return True


class Solution:
    def isPossible(self, nums: list[int]) -> bool:
        return solve(nums)
