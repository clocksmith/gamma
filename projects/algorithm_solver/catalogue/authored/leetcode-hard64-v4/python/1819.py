"""1819. Number of Different Subsequences GCDs."""

from math import gcd


def solve(nums: list[int]) -> int:
    """Sieve of present multiples; O(n + M log(M)^2) time and O(M) space, M=max(nums). Inputs are preserved."""
    maximum = max(nums)
    present = bytearray(maximum + 1)
    for value in nums:
        present[value] = 1
    answer = 0
    for candidate in range(1, maximum + 1):
        common = 0
        for multiple in range(candidate, maximum + 1, candidate):
            if present[multiple]:
                common = gcd(common, multiple)
                if common == candidate:
                    answer += 1
                    break
    return answer


class Solution:
    def countDifferentSubsequenceGCDs(self, nums: list[int]) -> int:
        return solve(nums)
