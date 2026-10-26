"""3336. Find the Number of Subsequences With Equal GCD: assign each index to neither or exactly one of two gcd states."""

from math import gcd


def solve(nums: list[int]) -> int:
    """O(n*M^2 + M^2 log M) time and O(M^2) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    maximum = max(nums)
    size = maximum + 1
    common = [[gcd(first, second) for second in range(size)] for first in range(size)]
    ways = [[0] * size for _ in range(size)]
    ways[0][0] = 1
    for value in nums:
        following = [row.copy() for row in ways]
        transform = common[value]
        for first in range(size):
            next_first = transform[first]
            for second, count in enumerate(ways[first]):
                if count:
                    next_second = transform[second]
                    following[next_first][second] = (following[next_first][second] + count) % modulus
                    following[first][next_second] = (following[first][next_second] + count) % modulus
        ways = following
    # GCD zero denotes an empty subsequence and must not contribute.
    return sum(ways[value][value] for value in range(1, size)) % modulus


class Solution:
    def subsequencePairCount(self, nums: list[int]) -> int:
        return solve(nums)
