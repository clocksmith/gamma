"""415. Add Strings (Easy).

Specification: https://leetcode.com/problems/add-strings/description/
"""


def solve(num1: str, num2: str) -> str:
    """O(n + m) time and output space; decimal carry arithmetic without whole-string conversion."""
    first = len(num1) - 1
    second = len(num2) - 1
    carry = 0
    digits = []
    while first >= 0 or second >= 0 or carry > 0:
        total = carry
        if first >= 0:
            total += ord(num1[first]) - 48
            first -= 1
        if second >= 0:
            total += ord(num2[second]) - 48
            second -= 1
        digits.append(str(total % 10))
        carry = total // 10
    return ''.join(reversed(digits))


class Solution:
    def addStrings(self, num1: str, num2: str) -> str:
        return solve(num1, num2)
