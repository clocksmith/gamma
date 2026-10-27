"""3895. Count Digit Appearances
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-digit-appearances/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3895.Count%20Digit%20Appearances/README_EN.md
Complexity: O(total decimal digits) time; O(log max(nums)) temporary space.
Positive integers <= 1e6; input preserved.
"""

from __future__ import annotations

def solve(nums, digit):
    return sum(str(value).count(str(digit)) for value in nums)


class Solution:
    def countDigitOccurrences(self, nums, digit):
        return solve(nums, digit)
