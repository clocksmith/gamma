"""3082. Find the Sum of the Power of All Subsequences.

Weighted subset DP counts unused elements in two ways; O(n*k) time and O(k) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    modulus = 1_000_000_007
    ways = [1] + [0] * k
    for value in nums:
        following = [(2 * count) % modulus for count in ways]
        for total in range(value, k + 1):
            following[total] = (following[total] + ways[total - value]) % modulus
        ways = following
    return ways[k]


class Solution:
    def sumOfPower(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
