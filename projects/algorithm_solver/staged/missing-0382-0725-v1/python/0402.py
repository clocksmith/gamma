"""402. Remove K Digits. Monotone digit stack; O(n) time."""

def solve(num: str, k: int) -> str:
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    if k:
        del stack[-k:]
    return ''.join(stack).lstrip('0') or '0'


class Solution:
    def removeKdigits(self, num: str, k: int) -> str:
        return solve(num, k)
