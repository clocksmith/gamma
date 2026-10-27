"""3952. Maximum Total Value of Covered Indices
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-total-value-of-covered-indices/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3952.Maximum%20Total%20Value%20of%20Covered%20Indices/README_EN.md
Complexity: O(n) time, O(n) Python temporary space and O(1) JavaScript auxiliary space.
A run of r tokens can cover any r positions of its r+1-position left extension; positive values favor distinct coverage. Each token moves at most once. Inputs preserved; native method pending.
"""

from __future__ import annotations

def solve(nums, s):
    total = 0
    index = 0
    while index < len(nums):
        if s[index] == '0':
            index += 1
            continue
        start = index
        while index < len(nums) and s[index] == '1':
            index += 1
        if start == 0:
            total += sum(nums[:index])
        else:
            segment = nums[start - 1:index]
            total += sum(segment) - min(segment)
    return total
