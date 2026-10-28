"""1684. Count the Number of Consistent Strings (Easy).

Specification: https://leetcode.com/problems/count-the-number-of-consistent-strings/description/
"""


def solve(allowed: str, words: list[str]) -> int:
    allowed_set = set(allowed)
    return sum(1 for word in words if all(ch in allowed_set for ch in word))


class Solution:
    def countConsistentStrings(self, allowed: str, words: list[str]) -> int:
        return solve(allowed, words)
