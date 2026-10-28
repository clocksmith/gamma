"""1073. Adding Two Negabinary Numbers (Medium).

Specification: https://leetcode.com/problems/adding-two-negabinary-numbers/description/
"""


def solve(arr1: list[int], arr2: list[int]) -> list[int]:
    result = []
    i, j = len(arr1) - 1, len(arr2) - 1
    carry = 0
    while i >= 0 or j >= 0 or carry != 0:
        total = carry
        if i >= 0:
            total += arr1[i]
            i -= 1
        if j >= 0:
            total += arr2[j]
            j -= 1
        digit = total % 2
        result.append(digit)
        carry = -(total - digit) // 2
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result[::-1]


class Solution:
    def addNegabinary(self, arr1: list[int], arr2: list[int]) -> list[int]:
        return solve(arr1, arr2)
