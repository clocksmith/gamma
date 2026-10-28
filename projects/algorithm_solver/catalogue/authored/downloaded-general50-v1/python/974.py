"""974. Subarray Sums Divisible by K (Medium).

Specification: https://leetcode.com/problems/subarray-sums-divisible-by-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    counts = {0: 1}
    prefix = 0
    total = 0
    for v in nums:
        prefix = (prefix + v) % k
        total += counts.get(prefix, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return total


class Solution:
    def subarraysDivByK(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
