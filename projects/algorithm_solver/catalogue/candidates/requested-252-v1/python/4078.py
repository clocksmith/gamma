"""4078. Three Fibonacci Sum
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/three-fibonacci-sum/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4078.Three%20Fibonacci%20Sum/README_EN.md
Complexity: O(log n) time, O(1) space.
F_i+F_(i+1)+F_(i+2)=2F_(i+2); the final term must be a positive Fibonacci number. No global precomputation.
"""

from __future__ import annotations

def solve(n):
    if n % 2:
        return False
    target = n//2
    a, b = 0, 1
    while b < target:
        a, b = b, a+b
    return b == target


class Solution:
    def threeFibonacciSum(self, n):
        return solve(n)
