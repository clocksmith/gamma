"""2446. Determine if Two Events Have Conflict (Easy).

Specification: https://leetcode.com/problems/determine-if-two-events-have-conflict/description/
"""


def solve(event1: list[str], event2: list[str]) -> bool:
    """O(1) time and space; zero-padded HH:MM strings compare chronologically; endpoints are inclusive."""
    return event1[0] <= event2[1] and event2[0] <= event1[1]


class Solution:
    def haveConflict(self, event1: list[str], event2: list[str]) -> bool:
        return solve(event1, event2)
