"""2389. Longest Subsequence With Limited Sum (Easy).

Specification: https://leetcode.com/problems/longest-subsequence-with-limited-sum/description/
"""


def solve(nums: list[int], queries: list[int]) -> list[int]:
    """O(n log n + q log n) time, O(n + q) space; binary-search sorted positive prefix sums; preserve inputs."""
    values = sorted(nums)
    prefix = []
    total = 0
    for value in values:
        total += value
        prefix.append(total)
    result = []
    for limit in queries:
        low = 0
        high = len(prefix)
        while low < high:
            middle = low + (high - low) // 2
            if prefix[middle] <= limit:
                low = middle + 1
            else:
                high = middle
        result.append(low)
    return result


class Solution:
    def answerQueries(self, nums: list[int], queries: list[int]) -> list[int]:
        return solve(nums, queries)
