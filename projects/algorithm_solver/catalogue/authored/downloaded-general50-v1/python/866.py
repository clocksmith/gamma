"""866. Prime Palindrome (Medium).

Specification: https://leetcode.com/problems/prime-palindrome/description/
"""


def _is_prime(x):
    if x < 2:
        return False
    if x == 2:
        return True
    if x % 2 == 0:
        return False
    d = 3
    while d * d <= x:
        if x % d == 0:
            return False
        d += 2
    return True


def _is_palindrome(x):
    s = str(x)
    return s == s[::-1]


def solve(n: int) -> int:
    x = n
    while True:
        if _is_palindrome(x) and _is_prime(x):
            return x
        x += 1


class Solution:
    def primePalindrome(self, n: int) -> int:
        return solve(n)
