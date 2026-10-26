"""859. Buddy Strings (Easy).

Specification: https://leetcode.com/problems/buddy-strings/description/
"""


def solve(s: str, goal: str) -> bool:
    """O(n) time, O(1) space for lowercase English; exactly one swap must be possible."""
    if len(s) != len(goal):
        return False
    mismatches = []
    seen = set()
    has_duplicate = False
    for index, character in enumerate(s):
        if character in seen:
            has_duplicate = True
        seen.add(character)
        if character != goal[index]:
            mismatches.append(index)
            if len(mismatches) > 2:
                return False
    if not mismatches:
        return has_duplicate
    if len(mismatches) != 2:
        return False
    first, second = mismatches
    return s[first] == goal[second] and s[second] == goal[first]


class Solution:
    def buddyStrings(self, s: str, goal: str) -> bool:
        return solve(s, goal)
