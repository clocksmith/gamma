"""2171. Removing Minimum Number of Magic Beans: choose the retained nonempty bag size from a sorted copy."""


def solve(beans: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(beans)
    total = sum(ordered)
    best = total
    for index, value in enumerate(ordered):
        best = min(best, total - value * (len(ordered) - index))
    return best


class Solution:
    def minimumRemoval(self, beans: list[int]) -> int:
        return solve(beans)
