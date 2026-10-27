"""4075. Longest Resilient Subarray I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/longest-resilient-subarray-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4075.Longest%20Resilient%20Subarray%20I/README_EN.md
Complexity: O(n+R log k) time, O(1) space, R equal-residue runs.
Every deletion leaving a divisible sum forces all residues to agree. For run residue a, valid lengths satisfy L=1 modulo k/gcd(k,a). Select the largest such length within each run. Inputs preserved.
"""

from __future__ import annotations
from math import gcd

def solve(nums, k):
    answer, left = 1, 0
    while left < len(nums):
        residue = nums[left] % k
        right = left+1
        while right < len(nums) and nums[right] % k == residue:
            right += 1
        length = right-left
        period = k//gcd(k, residue)
        answer = max(answer, length-(length-1) % period)
        left = right
    return answer


class Solution:
    def resilientSubarray(self, nums, k):
        return solve(nums, k)
