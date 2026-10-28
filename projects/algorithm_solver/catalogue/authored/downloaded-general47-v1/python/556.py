"""556. Next Greater Element III (Medium).

Specification: https://leetcode.com/problems/next-greater-element-iii/description/
"""


def solve(n: int) -> int:
    digits = [int(ch) for ch in str(n)]
    pivot = -1
    for i in range(len(digits) - 2, -1, -1):
        if digits[i] < digits[i + 1]:
            pivot = i
            break
    if pivot == -1:
        return -1
    for i in range(len(digits) - 1, pivot, -1):
        if digits[i] > digits[pivot]:
            digits[i], digits[pivot] = digits[pivot], digits[i]
            break
    left, right = pivot + 1, len(digits) - 1
    while left < right:
        digits[left], digits[right] = digits[right], digits[left]
        left += 1
        right -= 1
    result = int("".join(str(d) for d in digits))
    return -1 if result > 2147483647 else result


class Solution:
    def nextGreaterElement(self, n: int) -> int:
        return solve(n)
