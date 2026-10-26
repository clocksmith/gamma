"""3146. Permutation Difference between Two Strings (Easy).

Specification: https://leetcode.com/problems/permutation-difference-between-two-strings/description/
"""


def solve(s: str, t: str) -> int:
    """O(n) time, O(1) alphabet space; strings are permutations of distinct lowercase letters."""
    positions = [0] * 26
    for index, character in enumerate(s):
        positions[ord(character) - ord('a')] = index
    difference = 0
    for index, character in enumerate(t):
        difference += abs(index - positions[ord(character) - ord('a')])
    return difference


class Solution:
    def findPermutationDifference(self, s: str, t: str) -> int:
        return solve(s, t)
