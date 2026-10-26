"""1641. Count Sorted Vowel Strings: count weak compositions of the length into five vowel multiplicities."""


def solve(n: int) -> int:
    """O(1) time and O(1) auxiliary space on the declared n <= 50 domain; inputs are read-only."""
    return (n + 1) * (n + 2) * (n + 3) * (n + 4) // 24


class Solution:
    def countVowelStrings(self, n: int) -> int:
        return solve(n)
