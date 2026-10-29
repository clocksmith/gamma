"""Hack2Hire 6789754f11318cc872dd83ec (Find Greatest Triple) over an INFERRED spec; qualification unknown."""


def solve(digits):
    # three places; place p must leave (2 - p) digits after its pick
    n, value, start = len(digits), 0, 0
    for place in range(3):
        end = n - (2 - place)
        best = start
        for i in range(start + 1, end):
            if digits[i] > digits[best]:
                best = i  # strict > keeps the leftmost maximum
        value = value * 10 + digits[best]
        start = best + 1
    return value


class Solution:
    def findGreatestTriple(self, digits):
        return solve(digits)
