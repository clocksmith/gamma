"""881. Boats to Save People (Medium).

Specification: https://leetcode.com/problems/boats-to-save-people/description/
"""


def solve(people: list[int], limit: int) -> int:
    ordered = sorted(people)
    left, right = 0, len(ordered) - 1
    boats = 0
    while left <= right:
        if ordered[left] + ordered[right] <= limit:
            left += 1
        right -= 1
        boats += 1
    return boats


class Solution:
    def numRescueBoats(self, people: list[int], limit: int) -> int:
        return solve(people, limit)
