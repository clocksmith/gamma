"""3074. Apple Redistribution into Boxes (Easy).

Specification: https://leetcode.com/problems/apple-redistribution-into-boxes/description/
"""


def solve(apple: list[int], capacity: list[int]) -> int:
    """O(n + m log m) time, O(m) space; preserve apple and capacity."""
    remaining = sum(apple)
    ordered = sorted(capacity, reverse=True)
    for index, space in enumerate(ordered):
        remaining -= space
        if remaining <= 0:
            return index + 1
    return -1


class Solution:
    def minimumBoxes(self, apple: list[int], capacity: list[int]) -> int:
        return solve(apple, capacity)
