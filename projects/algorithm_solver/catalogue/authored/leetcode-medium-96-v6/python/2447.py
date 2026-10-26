"""2447. Number of Subarrays With GCD Equal to K: extend each starting point until its gcd can no longer be a multiple of k."""
from math import gcd


def solve(nums: list[int], k: int) -> int:
    """O(n^2 log U) time and O(1) auxiliary space for maximum value U; inputs are read-only."""
    answer = 0
    for left in range(len(nums)):
        current = 0
        for right in range(left, len(nums)):
            current = gcd(current, nums[right])
            if current % k:
                break
            if current == k:
                answer += 1
    return answer


class Solution:
    def subarrayGCD(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
