"""1704. Determine if String Halves Are Alike (Easy).

Specification: https://leetcode.com/problems/determine-if-string-halves-are-alike/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; recognize both uppercase and lowercase ASCII vowels."""
    vowels = 'aeiouAEIOU'
    half = len(s) // 2
    balance = 0
    for index, character in enumerate(s):
        if character in vowels:
            balance += 1 if index < half else -1
    return balance == 0


class Solution:
    def halvesAreAlike(self, s: str) -> bool:
        return solve(s)
