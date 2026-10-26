"""2399. Check Distances Between Same Letters (Easy).

Specification: https://leetcode.com/problems/check-distances-between-same-letters/description/
"""


def solve(s: str, distance: list[int]) -> bool:
    """O(n) time, O(1) alphabet space; each present letter occurs exactly twice."""
    first = [-1] * 26
    for index, character in enumerate(s):
        letter = ord(character) - ord('a')
        if first[letter] == -1:
            first[letter] = index
        elif index - first[letter] - 1 != distance[letter]:
            return False
    return True


class Solution:
    def checkDistances(self, s: str, distance: list[int]) -> bool:
        return solve(s, distance)
