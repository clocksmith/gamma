"""3969. Valid Subarrays With Matching Sum Digits I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/valid-subarrays-with-matching-sum-digits-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3969.Valid%20Subarrays%20With%20Matching%20Sum%20Digits%20I/README_EN.md
Complexity: O(n^2 + n log(sum(nums))) time, O(1) space.
Positive values make the decimal power monotone for each left endpoint. n <= 1500 and sum <= 1.5e12, exact Number arithmetic. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, x):
    answer = 0
    for left in range(len(nums)):
        total = 0
        power = 1
        for right in range(left, len(nums)):
            total += nums[right]
            while total >= power * 10:
                power *= 10
            if total % 10 == x and total // power == x:
                answer += 1
    return answer


class Solution:
    def countValidSubarrays(self, nums, x):
        return solve(nums, x)
