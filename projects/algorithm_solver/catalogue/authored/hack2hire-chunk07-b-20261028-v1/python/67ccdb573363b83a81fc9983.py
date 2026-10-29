"""Hack2Hire 67ccdb573363b83a81fc9983 (Pascal Triangle Encryption) over an INFERRED spec; qualification unknown."""

_SMALL = [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 2, 1, 0, 0], [1, 3, 3, 1, 0], [1, 4, 6, 4, 1]]  # C(a, b) for a, b < 5
_CRT = [[next(x for x in range(10) if x % 2 == r2 and x % 5 == r5) for r5 in range(5)] for r2 in range(2)]


def solve(digits):
    m = len(digits) - 2
    first = second = 0
    for i in range(m + 1):
        odd = 1 if i & m == i else 0  # Lucas mod 2
        r5, top, low = 1, m, i
        while low or top:
            x, y = top % 5, low % 5
            if y > x:
                r5 = 0
                break
            r5 = r5 * _SMALL[x][y] % 5
            top //= 5
            low //= 5
        coef = _CRT[odd][r5]
        if coef:
            first = (first + coef * (ord(digits[i]) - 48)) % 10
            second = (second + coef * (ord(digits[i + 1]) - 48)) % 10
    return str(first) + str(second)


class Solution:
    def encrypt(self, digits):
        return solve(digits)
