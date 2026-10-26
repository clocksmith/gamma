"""2418. Sort the People (Easy).

Specification: https://leetcode.com/problems/sort-the-people/description/
"""


def solve(names: list[str], heights: list[int]) -> list[str]:
    """O(n log n) time, O(n) space; preserve both arrays; heights are distinct."""
    order = sorted(range(len(names)), key=lambda index: heights[index], reverse=True)
    return [names[index] for index in order]


class Solution:
    def sortPeople(self, names: list[str], heights: list[int]) -> list[str]:
        return solve(names, heights)
