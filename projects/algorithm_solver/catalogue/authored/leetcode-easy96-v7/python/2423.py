"""2423. Remove Letter To Equalize Frequency (Easy).

Specification: https://leetcode.com/problems/remove-letter-to-equalize-frequency/description/
"""


def solve(word: str) -> bool:
    """O(n + 26^2) time, O(26) space; try removing one occurrence of each present letter."""
    counts = [0] * 26
    for character in word:
        counts[ord(character) - 97] += 1
    for removed in range(26):
        if counts[removed] == 0:
            continue
        counts[removed] -= 1
        expected = 0
        valid = True
        for count in counts:
            if count == 0:
                continue
            if expected == 0:
                expected = count
            elif count != expected:
                valid = False
                break
        counts[removed] += 1
        if valid:
            return True
    return False


class Solution:
    def equalFrequency(self, word: str) -> bool:
        return solve(word)
