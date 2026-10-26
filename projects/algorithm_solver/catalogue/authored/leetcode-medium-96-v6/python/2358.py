"""2358. Maximum Number of Groups Entering a Competition: find the largest triangular group count since sorted positive grades can realize it."""


def solve(grades: list[int]) -> int:
    """O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only."""
    # Sorting conceptually yields groups of sizes 1, 2, ... with increasing sums.
    size = len(grades)
    low, high = 0, size
    while low < high:
        middle = (low + high + 1) // 2
        if middle * (middle + 1) // 2 <= size:
            low = middle
        else:
            high = middle - 1
    return low


class Solution:
    def maximumGroups(self, grades: list[int]) -> int:
        return solve(grades)
