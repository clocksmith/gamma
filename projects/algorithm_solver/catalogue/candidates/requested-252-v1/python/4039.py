"""4039. Sum of Decoded Numbers
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/sum-of-decoded-numbers/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4039.Sum%20of%20Decoded%20Numbers/README_EN.md
Complexity: O(n log(max exponent)) time, O(log(max encoded value)) temporary space.
Valid encoded inputs below 10^15 are exact JS Numbers. Modular multiplication uses exact split products. Inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    answer = 0
    modulus = 1_000_000_007
    for value in nums:
        encoded = str(value)
        width = int(encoded[-1])
        digits = encoded[:-1]
        x, y = int(digits[:width]), int(digits[width:])
        answer = (answer + pow(x, y, modulus)) % modulus
    return answer


class Solution:
    def sumDecoded(self, nums):
        return solve(nums)
