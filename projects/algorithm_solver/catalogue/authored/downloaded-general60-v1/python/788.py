"""788. Rotated Digits (Medium).

Specification: https://leetcode.com/problems/rotated-digits/description/
"""


def solve(n: int) -> int:
    valid = set('0125689')
    changing = set('2569')
    count = 0
    for value in range(1, n + 1):
        text = str(value)
        if all(ch in valid for ch in text) and any(ch in changing for ch in text):
            count += 1
    return count


class Solution:
    def rotatedDigits(self, n: int) -> int:
        return solve(n)
