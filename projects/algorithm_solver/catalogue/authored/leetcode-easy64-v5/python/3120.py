"""3120. Count the Number of Special Characters I (Easy).

Specification: https://leetcode.com/problems/count-the-number-of-special-characters-i/description/
"""


def solve(word: str) -> int:
    """O(n) time, O(1) alphabet space; order of lowercase and uppercase occurrences is irrelevant."""
    lower = [False] * 26
    upper = [False] * 26
    for character in word:
        code = ord(character)
        if code >= ord('a'):
            lower[code - ord('a')] = True
        else:
            upper[code - ord('A')] = True
    count = 0
    for index in range(26):
        if lower[index] and upper[index]:
            count += 1
    return count


class Solution:
    def numberOfSpecialChars(self, word: str) -> int:
        return solve(word)
