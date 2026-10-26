"""3015. Count the Number of Houses at a Certain Distance I: compare the direct path with each orientation of the extra edge."""


def solve(n: int, x: int, y: int) -> list[int]:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    counts = [0] * n
    for left in range(1, n + 1):
        for right in range(left + 1, n + 1):
            distance = min(right - left,
                           abs(left - x) + 1 + abs(right - y),
                           abs(left - y) + 1 + abs(right - x))
            counts[distance - 1] += 2
    return counts


class Solution:
    def countOfPairs(self, n: int, x: int, y: int) -> list[int]:
        return solve(n, x, y)
