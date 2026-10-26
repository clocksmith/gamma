"""3852. Smallest Pair With Different Frequencies (Easy).

Specification: https://leetcode.com/problems/smallest-pair-with-different-frequencies/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n + 100) time, O(100) space; preserve nums and return the lexicographically smallest pair."""
    counts = [0] * 101
    for value in nums:
        counts[value] += 1
    smallest = 1
    while counts[smallest] == 0:
        smallest += 1
    for value in range(smallest + 1, 101):
        if counts[value] > 0 and counts[value] != counts[smallest]:
            return [smallest, value]
    return [-1, -1]


class Solution:
    def minDistinctFreqPair(self, nums: list[int]) -> list[int]:
        return solve(nums)
