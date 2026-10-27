"""3927. Minimize Array Sum Using Divisible Replacements
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimize-array-sum-using-divisible-replacements/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3927.Minimize%20Array%20Sum%20Using%20Divisible%20Replacements/README_EN.md
Complexity: O(M log M+n) time, O(M+n) space.
Each value reduces to the smallest originally present divisor, not necessarily the global minimum. Inputs preserved; native name pending.
"""

from __future__ import annotations

def solve(nums):
    maximum = max(nums)
    present = set(nums)
    smallest = [0] * (maximum + 1)
    for divisor in range(1, maximum + 1):
        if divisor in present and smallest[divisor] == 0:
            for multiple in range(divisor, maximum + 1, divisor):
                if smallest[multiple] == 0:
                    smallest[multiple] = divisor
    return sum(smallest[value] for value in nums)
