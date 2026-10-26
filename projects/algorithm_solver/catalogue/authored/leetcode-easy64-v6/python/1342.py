"""1342. Number of Steps to Reduce a Number to Zero (Easy).

Specification: https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/description/
"""


def solve(num: int) -> int:
    """O(log(num + 1)) time, O(1) space; use integer arithmetic."""
    remaining = num
    result = 0
    while remaining > 0:
        remaining = remaining // 2 if remaining % 2 == 0 else remaining - 1
        result += 1
    return result


class Solution:
    def numberOfSteps(self, num: int) -> int:
        return solve(num)
