"""2470. Number of Subarrays With LCM Equal to K: extend each subarray while its least common multiple remains a divisor of k."""
from math import gcd


def solve(nums: list[int], k: int) -> int:
    """O(n^2 log(k + 1)) time and O(1) auxiliary space; inputs are read-only."""
    answer = 0
    for left in range(len(nums)):
        current = 1
        for right in range(left, len(nums)):
            value = nums[right]
            if k % value:
                break
            current = current // gcd(current, value) * value
            if current > k or k % current:
                break
            if current == k:
                answer += 1
    return answer


class Solution:
    def subarrayLCM(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
