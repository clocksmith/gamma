"""60. Permutation Sequence (Hard).

Specification: https://leetcode.com/problems/permutation-sequence/description/
"""


def solve(n: int, k: int) -> str:
    numbers = list(range(1, n + 1))
    factorial = 1
    for i in range(2, n):
        factorial *= i
    remaining = k - 1
    result = ''
    for i in range(n, 0, -1):
        index = remaining // factorial if factorial else 0
        result += str(numbers.pop(index))
        remaining %= factorial if factorial else 1
        if i > 1:
            factorial //= (i - 1)
    return result


class Solution:
    def getPermutation(self, n: int, k: int) -> str:
        return solve(n, k)
