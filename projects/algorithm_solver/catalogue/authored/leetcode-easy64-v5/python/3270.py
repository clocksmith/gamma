"""3270. Find the Key of the Numbers (Easy).

Specification: https://leetcode.com/problems/find-the-key-of-the-numbers/description/
"""


def solve(num1: int, num2: int, num3: int) -> int:
    """O(1) time and space for four-digit inputs; implicit leading zeros participate."""
    first, second, third = num1, num2, num3
    result = 0
    place = 1
    for _ in range(4):
        result += min(first % 10, second % 10, third % 10) * place
        first //= 10
        second //= 10
        third //= 10
        place *= 10
    return result


class Solution:
    def generateKey(self, num1: int, num2: int, num3: int) -> int:
        return solve(num1, num2, num3)
