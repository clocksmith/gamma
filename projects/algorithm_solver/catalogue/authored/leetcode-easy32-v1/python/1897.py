"""1897. Redistribute Characters to Make All Strings Equal (Easy).

Specification: https://leetcode.com/problems/redistribute-characters-to-make-all-strings-equal/description/
"""


def solve(words: list[str]) -> bool:
    """O(total characters) time, O(1) alphabet space; preserve words."""
    counts = [0] * 26
    for word in words:
        for character in word:
            counts[ord(character) - ord('a')] += 1
    for count in counts:
        if count % len(words) != 0:
            return False
    return True


class Solution:
    def makeEqual(self, words: list[str]) -> bool:
        return solve(words)
