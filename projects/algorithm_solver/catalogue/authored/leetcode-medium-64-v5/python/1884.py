"""1884. Egg Drop With 2 Eggs and N Floors: find the smallest triangular coverage that reaches the final floor."""


def solve(n: int) -> int:
    """O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only."""
    low, high = 1, n
    while low < high:
        middle = (low + high) // 2
        if middle * (middle + 1) // 2 >= n:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def twoEggDrop(self, n: int) -> int:
        return solve(n)
