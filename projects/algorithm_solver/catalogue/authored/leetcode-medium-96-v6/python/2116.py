"""2116. Check if a Parentheses String Can Be Valid: track the interval of feasible open-parenthesis counts."""


def solve(s: str, locked: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    if len(s) % 2:
        return False
    low = high = 0
    for character, fixed in zip(s, locked):
        if fixed == '0':
            low -= 1
            high += 1
        elif character == '(':
            low += 1
            high += 1
        else:
            low -= 1
            high -= 1
        if high < 0:
            return False
        low = max(low, 0)
    return low == 0


class Solution:
    def canBeValid(self, s: str, locked: str) -> bool:
        return solve(s, locked)
