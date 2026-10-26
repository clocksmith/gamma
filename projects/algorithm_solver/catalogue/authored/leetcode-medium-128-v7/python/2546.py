"""2546. Apply Bitwise Operations to Make Strings Equal: compare whether each string has a one that can generate and remove other bits."""


def solve(s: str, target: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    return ('1' in s) == ('1' in target)


class Solution:
    def makeStringsEqual(self, s: str, target: str) -> bool:
        return solve(s, target)
