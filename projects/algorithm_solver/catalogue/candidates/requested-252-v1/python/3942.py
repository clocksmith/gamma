"""3942. Minimum Operations to Sort a Permutation
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-operations-to-sort-a-permutation/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3942.Minimum%20Operations%20to%20Sort%20a%20Permutation/README_EN.md
Complexity: O(n) time, O(1) auxiliary space.
Only whole reversal and one-step LEFT rotation. Permutation 0..n-1, input preserved.
"""

from __future__ import annotations

def solve(nums):
    n = len(nums)
    zero = nums.index(0)
    answer = float('inf')
    if all(nums[(zero + offset) % n] == offset for offset in range(n)):
        answer = min(zero, n - zero + 2)
    if all(nums[(zero - offset) % n] == offset for offset in range(n)):
        answer = min(answer, zero + 2, n - zero)
    return -1 if answer == float('inf') else answer


class Solution:
    def minOperations(self, nums):
        return solve(nums)
