"""1963. Minimum Number of Swaps to Make the String Balanced: pair unmatched closing brackets two at a time."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    opened = unmatched = 0
    for bracket in s:
        if bracket == '[':
            opened += 1
        elif opened > 0:
            opened -= 1
        else:
            unmatched += 1
    return (unmatched + 1) // 2


class Solution:
    def minSwaps(self, s: str) -> int:
        return solve(s)
