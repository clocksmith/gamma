"""Hack2Hire 67883eb4e20f8f324213c2a2 (Next Greater Palindrome) over an INFERRED spec; qualification unknown."""


def solve(n):
    length = len(n)
    if n.count('9') == length:
        return '1' + '0' * (length - 1) + '1'
    half = n[:(length + 1) // 2]
    mirror = half + half[:length // 2][::-1]
    if mirror > n:
        return mirror
    digits = list(half)
    i = len(digits) - 1
    while digits[i] == '9':
        digits[i] = '0'
        i -= 1
    digits[i] = chr(ord(digits[i]) + 1)
    half = ''.join(digits)
    return half + half[:length // 2][::-1]


class Solution:
    def nextGreaterPalindrome(self, n):
        return solve(n)
