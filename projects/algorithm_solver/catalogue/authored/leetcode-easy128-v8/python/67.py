"""67. Add Binary (Easy).

Specification: https://leetcode.com/problems/add-binary/description/
"""


def solve(a: str, b: str) -> str:
    """O(n + m) time and space; add digits without converting whole strings to integers."""
    result = []
    left, right = len(a) - 1, len(b) - 1
    carry = 0
    while left >= 0 or right >= 0 or carry:
        total = carry
        if left >= 0:
            total += ord(a[left]) - 48
            left -= 1
        if right >= 0:
            total += ord(b[right]) - 48
            right -= 1
        result.append(str(total % 2))
        carry = total // 2
    return ''.join(reversed(result))


class Solution:
    def addBinary(self, a: str, b: str) -> str:
        return solve(a, b)
