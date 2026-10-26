"""1331. Rank Transform of an Array (Easy).

Specification: https://leetcode.com/problems/rank-transform-of-an-array/description/
"""


def solve(arr: list[int]) -> list[int]:
    """O(n log n) time, O(n) space; preserve arr and return a fresh array."""
    values = sorted(set(arr))
    ranks = {value: index + 1 for index, value in enumerate(values)}
    return [ranks[value] for value in arr]


class Solution:
    def arrayRankTransform(self, arr: list[int]) -> list[int]:
        return solve(arr)
