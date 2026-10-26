"""904. Fruit Into Baskets: maintain the longest window containing at most two values."""


def solve(fruits: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    counts = {}
    left = best = 0
    for right, value in enumerate(fruits):
        counts[value] = counts.get(value, 0) + 1
        while len(counts) > 2:
            outgoing = fruits[left]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                del counts[outgoing]
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def totalFruit(self, fruits: list[int]) -> int:
        return solve(fruits)
