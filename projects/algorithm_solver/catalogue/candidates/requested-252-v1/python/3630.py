"""3630. Partition Array for Maximum XOR and AND.

Specification: https://leetcode.com/problems/partition-array-for-maximum-xor-and-and/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(2^n * n * 30) time, O(2^n + 30) space; n <= 19 and values < 2^30.
Inputs are not modified.
For fixed B, XOR(A) + XOR(C) = totalXor + 2 * (XOR(A) & ~totalXor); a projected linear basis maximizes the second term.
"""

def solve(nums):
    size = 1 << len(nums)
    full = size - 1
    xors = [0] * size
    ands = [0] * size
    for subset in range(1, size):
        bit = subset & -subset
        value = nums[bit.bit_length() - 1]
        rest = subset ^ bit
        xors[subset] = xors[rest] ^ value
        ands[subset] = ands[rest] & value if rest else value
    answer = 0
    for remaining in range(size):
        total_xor = xors[remaining]
        basis = [0] * 30
        bits = remaining
        while bits:
            bit = bits & -bits
            bits ^= bit
            value = nums[bit.bit_length() - 1] & ~total_xor
            while value:
                leading = value.bit_length() - 1
                if basis[leading]:
                    value ^= basis[leading]
                else:
                    basis[leading] = value
                    break
        best = 0
        for value in reversed(basis):
            best = max(best, best ^ value)
        answer = max(answer, ands[full ^ remaining] + total_xor + 2 * best)
    return answer


class Solution:
    def maximizeXorAndXor(self, nums):
        return solve(nums)
