"""3645. Maximum Total from Optimal Activation Order.

Specification: https://leetcode.com/problems/maximum-total-from-optimal-activation-order/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n log n) time, O(n) space; for each limit L, at most L values can activate before that group disappears.
Inputs are not modified.
"""

def solve(value, limit):
    groups = {}
    for score, capacity in zip(value, limit):
        groups.setdefault(capacity, []).append(score)
    return sum(sum(sorted(scores, reverse=True)[:capacity]) for capacity, scores in groups.items())


class Solution:
    def maxTotal(self, value, limit):
        return solve(value, limit)
