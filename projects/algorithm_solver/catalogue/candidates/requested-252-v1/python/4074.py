"""4074. Maximum Product Pair With Target Sum
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-product-pair-with-target-sum/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4074.Maximum%20Product%20Pair%20With%20Target%20Sum/README_EN.md
Complexity: O(n) expected time, O(n) space.
Return indices, larger value first. Equal-value pairs are forbidden even at distinct indices. Negative products remain eligible; any maximum-product tie is valid. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, target):
    first = {}
    answer = [-1, -1]
    best = float('-inf')
    for index, value in enumerate(nums):
        other = target-value
        if other != value and other in first:
            product = value*other
            if product > best:
                best = product
                answer = [index, first[other]] if value > other else [first[other], index]
        first.setdefault(value, index)
    return answer
