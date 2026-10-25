"""2186. Minimum Number of Steps to Make Two Strings Anagram II: sum the unmatched counts in both strings."""


def solve(s: str, t: str) -> int:
    """O(len(s) + len(t)) time and O(1) auxiliary space for lowercase English letters; inputs are read-only."""
    differences = [0] * 26
    for character in s:
        differences[ord(character) - ord("a")] += 1
    for character in t:
        differences[ord(character) - ord("a")] -= 1
    return sum(abs(difference) for difference in differences)


class Solution:
    def minSteps(self, s: str, t: str) -> int:
        return solve(s, t)
