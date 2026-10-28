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


def solve(n: int) -> int:
    # Every even-digit palindrome is divisible by 11; only 11 is prime.
    for small in (2, 3, 5, 7, 11):
        if n <= small:
            return small
    digits = len(str(n))
    if digits % 2 == 0:
        digits += 1
    while True:
        half = (digits + 1) // 2
        first = max(10 ** (half - 1), int(str(n)[:half]) if len(str(n)) == digits else 0)
        for prefix in range(first, 10 ** half):
            text = str(prefix)
            palindrome = int(text + text[-2::-1])
            if palindrome >= n and _is_prime(palindrome):
                return palindrome
        digits += 2


class Solution:
    def primePalindrome(self, n: int) -> int:
        return solve(n)
