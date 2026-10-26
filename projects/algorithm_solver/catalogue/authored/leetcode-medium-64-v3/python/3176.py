"""3176. Find the Maximum Length of a Good Subsequence I: track best ending values for each permitted count of adjacent changes."""


def solve(nums: list[int], k: int) -> int:
    """O(n * (k + 1)) expected time and O(u * (k + 1)) space for u distinct values; inputs are read-only."""
    endings = {}
    best = [0] * (k + 1)
    for value in nums:
        if value not in endings:
            endings[value] = [0] * (k + 1)
        same = endings[value]
        # Descending budgets keep best[changes - 1] from reusing this occurrence.
        for changes in range(k, -1, -1):
            candidate = same[changes] + 1
            if changes:
                candidate = max(candidate, best[changes - 1] + 1)
            same[changes] = candidate
            best[changes] = max(best[changes], candidate)
    return best[k]


class Solution:
    def maximumLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
