"""3438. Find Valid Pair of Adjacent Digits in String (Easy).

Specification: https://leetcode.com/problems/find-valid-pair-of-adjacent-digits-in-string/description/
"""


def solve(s: str) -> str:
    """O(n) time, O(1) digit space; return the first qualifying adjacent pair."""
    counts = [0] * 10
    for character in s:
        counts[ord(character) - ord('0')] += 1
    for index in range(len(s) - 1):
        first = ord(s[index]) - ord('0')
        second = ord(s[index + 1]) - ord('0')
        if first != second and counts[first] == first and counts[second] == second:
            return s[index:index + 2]
    return ''


class Solution:
    def findValidPair(self, s: str) -> str:
        return solve(s)
