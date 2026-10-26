"""1358. Number of Substrings Containing All Three Characters: count valid starting positions from the last occurrence of each letter."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    last = [-1] * 3
    total = 0
    for index, letter in enumerate(s):
        last[ord(letter) - ord('a')] = index
        total += min(last) + 1
    return total


class Solution:
    def numberOfSubstrings(self, s: str) -> int:
        return solve(s)
