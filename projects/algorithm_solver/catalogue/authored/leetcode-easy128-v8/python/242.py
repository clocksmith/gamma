"""242. Valid Anagram (Easy).

Specification: https://leetcode.com/problems/valid-anagram/description/
"""


def solve(s: str, t: str) -> bool:
    """O(n + m) time, O(1) space for the declared lowercase-English alphabet."""
    if len(s) != len(t):
        return False
    counts = [0] * 26
    for first, second in zip(s, t):
        counts[ord(first) - 97] += 1
        counts[ord(second) - 97] -= 1
    return all(count == 0 for count in counts)


class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        return solve(s, t)
