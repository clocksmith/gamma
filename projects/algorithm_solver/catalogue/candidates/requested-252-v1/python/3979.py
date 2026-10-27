"""3979. Maximum Valid Pair Sum
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-valid-pair-sum/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3979.Maximum%20Valid%20Pair%20Sum/README_EN.md
Complexity: O(n) time, O(1) space.
Index gap at least k; a valid pair is guaranteed by 1 <= k < n. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, k):
    best_left = nums[0]
    answer = nums[0] + nums[k]
    for right in range(k, len(nums)):
        best_left = max(best_left, nums[right - k])
        answer = max(answer, best_left + nums[right])
    return answer


class Solution:
    def maxValidPairSum(self, nums, k):
        return solve(nums, k)
