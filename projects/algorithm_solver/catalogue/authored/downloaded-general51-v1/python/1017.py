"""1017. Convert to Base -2 (Medium).

Specification: https://leetcode.com/problems/convert-to-base-2/description/
"""


def solve(n: int) -> str:
    if n == 0:
        return '0'
    result = ''
    value = n
    while value != 0:
        remainder = value % 2
        if remainder < 0:
            remainder += 2
        result = str(remainder) + result
        value = (value - remainder) // -2
    return result


class Solution:
    def baseNeg2(self, n: int) -> str:
        return solve(n)
