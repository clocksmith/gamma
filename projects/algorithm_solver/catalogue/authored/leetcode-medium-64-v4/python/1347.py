"""1347. Minimum Number of Steps to Make Two Strings Anagram: sum positive letter deficits in the target string."""


def solve(s: str, t: str) -> int:
    """O(n) time and O(1) auxiliary space for the fixed lowercase alphabet; inputs are read-only."""
    counts = [0] * 26
    for letter in s:
        counts[ord(letter) - ord('a')] += 1
    for letter in t:
        counts[ord(letter) - ord('a')] -= 1
    return sum(max(0, count) for count in counts)


class Solution:
    def minSteps(self, s: str, t: str) -> int:
        return solve(s, t)
