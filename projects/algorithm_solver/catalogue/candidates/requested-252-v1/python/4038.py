"""4038. Count Integers Appearing in a Single Block
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-integers-appearing-in-a-single-block/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4038.Count%20Integers%20Appearing%20in%20a%20Single%20Block/README_EN.md
Complexity: O(n) expected time, O(distinct values) space.
Counts maximal blocks, not occurrences; inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    blocks = {}
    for i, x in enumerate(nums):
        if i == 0 or nums[i-1] != x:
            blocks[x] = blocks.get(x, 0) + 1
    return sum(count == 1 for count in blocks.values())


class Solution:
    def countSpecialIntegers(self, nums):
        return solve(nums)
