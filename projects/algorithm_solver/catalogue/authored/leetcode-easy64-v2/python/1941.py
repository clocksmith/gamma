"""1941. Check if All Characters Have Equal Number of Occurrences (Easy).

Specification: https://leetcode.com/problems/check-if-all-characters-have-equal-number-of-occurrences/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) alphabet space; s is nonempty and lowercase ASCII."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    expected = 0
    for count in counts:
        if count == 0:
            continue
        if expected == 0:
            expected = count
        elif count != expected:
            return False
    return True


class Solution:
    def areOccurrencesEqual(self, s: str) -> bool:
        return solve(s)
