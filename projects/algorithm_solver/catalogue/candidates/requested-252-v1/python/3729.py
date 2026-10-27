"""3729. Count Distinct Subarrays Divisible by K in Sorted Array
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-distinct-subarrays-divisible-by-k-in-sorted-array/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3729.Count%20Distinct%20Subarrays%20Divisible%20by%20K%20in%20Sorted%20Array/README_EN.md
Complexity: O(n + g log k) time for g equal-value runs; O(n) space.
Assumes supplied nondecreasing input. Distinctness is by sequence, not endpoint pair; integer counts fit Number.
"""

from __future__ import annotations
from math import gcd

def solve(nums, k):
    counts = {0: 1}
    remainder = answer = 0
    for value in nums:
        remainder = (remainder + value) % k
        answer += counts.get(remainder, 0)
        counts[remainder] = counts.get(remainder, 0) + 1
    start = 0
    while start < len(nums):
        end = start + 1
        while end < len(nums) and nums[end] == nums[start]:
            end += 1
        length = end - start
        period = k // gcd(k, nums[start])
        valid_lengths = length // period
        answer -= valid_lengths * length - period * valid_lengths * (valid_lengths + 1) // 2
        start = end
    return answer


class Solution:
    def numGoodSubarrays(self, nums, k):
        return solve(nums, k)
