"""3649. Number of Perfect Pairs.

Specification: https://leetcode.com/problems/number-of-perfect-pairs/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n log n) time, O(n) space; conditions reduce to max(abs(a),abs(b)) <= 2 * min(abs(a),abs(b)).
Inputs are not modified.
"""

def solve(nums):
    values = sorted(map(abs, nums))
    left = answer = 0
    for right, value in enumerate(values):
        while 2 * values[left] < value:
            left += 1
        answer += right - left
    return answer


class Solution:
    def perfectPairs(self, nums):
        return solve(nums)
