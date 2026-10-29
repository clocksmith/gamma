"""Hack2Hire 69c0a3ed21f6ab42269647c2 (Fancy Number). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(n):
    digits = []
    while n:
        digits.append(n % 4)
        n //= 4
    count = 0
    for position in range(len(digits) - 1, -1, -1):
        digit = digits[position]
        if digit == 1:
            count += 1 << position
        elif digit >= 2:
            count += 1 << (position + 1)
            break
    return count - 1


class Solution:
    def countFancyNumbers(self, n):
        return solve(n)
