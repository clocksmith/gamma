"""2183. Count Array Pairs Divisible by K."""

from math import gcd


def solve(nums: list[int], k: int) -> int:
    """Group previous values by gcd(value,k); O(n*(tau(k)+log k)) time and O(tau(k)) space. Inputs are preserved."""
    frequency = {}
    answer = 0
    for value in nums:
        common = gcd(value, k)
        for previous, count in frequency.items():
            if common * previous % k == 0:
                answer += count
        frequency[common] = frequency.get(common, 0) + 1
    return answer


class Solution:
    def countPairs(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
