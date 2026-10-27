"""3644. Maximum K to Sort a Permutation.

Specification: https://leetcode.com/problems/maximum-k-to-sort-a-permutation/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n) time, O(1) space; bitwise AND of all misplaced permutation values.
Inputs are not modified.
"""

def solve(nums):
    answer = None
    for index, value in enumerate(nums):
        if value != index:
            answer = value if answer is None else answer & value
    return 0 if answer is None else answer


class Solution:
    def sortPermutation(self, nums):
        return solve(nums)
