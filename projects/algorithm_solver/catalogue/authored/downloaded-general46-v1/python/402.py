"""402. Remove K Digits (Medium).

Specification: https://leetcode.com/problems/remove-k-digits/description/
"""


def solve(num: str, k: int) -> str:
    stack = []
    for ch in num:
        while k > 0 and stack and stack[-1] > ch:
            stack.pop()
            k -= 1
        stack.append(ch)
    while k > 0:
        stack.pop()
        k -= 1
    result = "".join(stack).lstrip('0')
    return result if result else '0'


class Solution:
    def removeKdigits(self, num: str, k: int) -> str:
        return solve(num, k)
