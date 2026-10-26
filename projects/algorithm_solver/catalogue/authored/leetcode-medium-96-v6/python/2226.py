"""2226. Maximum Candies Allocated to K Children: binary search the largest equal portion supported by splitting the piles."""


def solve(candies: list[int], k: int) -> int:
    """O(n log M) time and O(1) auxiliary space for maximum pile M; inputs are read-only."""
    low, high = 0, max(candies)
    while low < high:
        middle = (low + high + 1) // 2
        portions = 0
        for pile in candies:
            portions += pile // middle
            if portions >= k:
                break
        if portions >= k:
            low = middle
        else:
            high = middle - 1
    return low


class Solution:
    def maximumCandies(self, candies: list[int], k: int) -> int:
        return solve(candies, k)
