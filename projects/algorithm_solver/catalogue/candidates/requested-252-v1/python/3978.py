"""3978. Unique Middle Element
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/unique-middle-element/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3978.Unique%20Middle%20Element/README_EN.md
Complexity: O(n) time, O(1) space.
Middle position in the original odd-length array, not the sorted median. Input preserved.
"""

from __future__ import annotations

def solve(nums):
    return nums.count(nums[len(nums) // 2]) == 1


class Solution:
    def isMiddleElementUnique(self, nums):
        return solve(nums)
