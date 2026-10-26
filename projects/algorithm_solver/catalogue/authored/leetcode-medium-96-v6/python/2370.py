"""2370. Longest Ideal Subsequence: retain the longest subsequence ending in each alphabet letter."""


def solve(s: str, k: int) -> int:
    """O(n * min(26, 2k + 1)) time and O(26) auxiliary space; inputs are read-only."""
    best = [0] * 26
    for character in s:
        letter = ord(character) - ord('a')
        length = 0
        for previous in range(max(0, letter - k), min(26, letter + k + 1)):
            length = max(length, best[previous])
        best[letter] = length + 1
    return max(best)


class Solution:
    def longestIdealString(self, s: str, k: int) -> int:
        return solve(s, k)
