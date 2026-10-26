"""3312. Sorted GCD Pair Queries: count exact gcds by subtracting proper multiples."""

from bisect import bisect_right


def solve(nums: list[int], queries: list[int]) -> list[int]:
    """O(n + M log M + q log M) time and O(M + q) space. Inputs are preserved."""
    maximum = max(nums)
    frequency = [0] * (maximum + 1)
    for value in nums:
        frequency[value] += 1
    exact = [0] * (maximum + 1)
    for divisor in range(maximum, 0, -1):
        count = sum(frequency[multiple] for multiple in range(divisor, maximum + 1, divisor))
        exact[divisor] = count * (count - 1) // 2
        for multiple in range(2 * divisor, maximum + 1, divisor):
            exact[divisor] -= exact[multiple]
    for divisor in range(1, maximum + 1):
        exact[divisor] += exact[divisor - 1]
    return [bisect_right(exact, rank) for rank in queries]


class Solution:
    def gcdValues(self, nums: list[int], queries: list[int]) -> list[int]:
        return solve(nums, queries)
