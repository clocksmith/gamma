"""1486. XOR Operation in an Array (Easy).

Specification: https://leetcode.com/problems/xor-operation-in-an-array/description/
"""


def solve(n: int, start: int) -> int:
    """O(n) time, O(1) space; all operands fit signed int32 in the public domain."""
    result = 0
    for index in range(n):
        result ^= start + 2 * index
    return result


class Solution:
    def xorOperation(self, n: int, start: int) -> int:
        return solve(n, start)
