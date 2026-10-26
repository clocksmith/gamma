"""2606. Find the Substring With Maximum Cost: run maximum-subarray accumulation over the declared character costs."""


def solve(s: str, chars: str, vals: list[int]) -> int:
    """O(n + m) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only."""
    costs = list(range(1, 27))
    for character, value in zip(chars, vals):
        costs[ord(character) - ord('a')] = value
    current = best = 0
    for character in s:
        current = max(0, current + costs[ord(character) - ord('a')])
        best = max(best, current)
    return best


class Solution:
    def maximumCostSubstring(self, s: str, chars: str, vals: list[int]) -> int:
        return solve(s, chars, vals)
