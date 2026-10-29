"""Hack2Hire 68fd47ba47bea664c0bba33c (Circular Prime Number Check) over an INFERRED spec; qualification unknown."""


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    d = 5
    while d * d <= n:
        if n % d == 0 or n % (d + 2) == 0:
            return False
        d += 6
    return True


def solve(n):
    digits, power = 1, 1
    while power * 10 <= n:
        power *= 10
        digits += 1
    r = n
    for _ in range(digits):
        if not is_prime(r):
            return False
        r = (r % power) * 10 + r // power
    return True


class Solution:
    def isCircularPrime(self, n):
        return solve(n)
