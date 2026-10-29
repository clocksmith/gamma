"""Hack2Hire 6854bafdc201117d348a25d2 (Maximize Number With K Swaps) over an INFERRED spec; qualification unknown."""


def solve(s, k):
    digits = list(s)
    left = k
    for i in range(len(digits)):
        if left == 0:
            break
        if digits[i] < '5':
            digits[i] = '5'
            left -= 1
    return ''.join(digits)


class Solution:
    def maximizeNumber(self, s, k):
        return solve(s, k)
