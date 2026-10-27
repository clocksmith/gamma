"""3653. XOR After Range Multiplication Queries I.

Specification: https://leetcode.com/problems/xor-after-range-multiplication-queries-i/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n + total updated positions) time, O(n) space; modular multiplication is exact.
Inputs are not modified.
"""

def solve(nums, queries):
    values = list(nums)
    modulus = 1000000007
    for left, right, step, multiplier in queries:
        for index in range(left, right + 1, step):
            values[index] = values[index] * multiplier % modulus
    answer = 0
    for value in values:
        answer ^= value
    return answer


class Solution:
    def xorAfterQueries(self, nums, queries):
        return solve(nums, queries)
