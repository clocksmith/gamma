"""2363. Merge Similar Items (Easy).

Specification: https://leetcode.com/problems/merge-similar-items/description/
"""


def solve(items1: list[list[int]], items2: list[list[int]]) -> list[list[int]]:
    """O(n + m + u log u) time, O(u) space; sum weights by value; return fresh pairs sorted by value."""
    weights = {}
    for items in (items1, items2):
        for value, weight in items:
            weights[value] = weights.get(value, 0) + weight
    return [[value, weights[value]] for value in sorted(weights)]


class Solution:
    def mergeSimilarItems(self, items1: list[list[int]], items2: list[list[int]]) -> list[list[int]]:
        return solve(items1, items2)
