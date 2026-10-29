"""Hack2Hire 6862ed30eb0810914237aaf3 (Add Signed Arrays) over an INFERRED spec; qualification unknown."""


def parse(chars):
    sign, start, value = 1, 0, 0
    if chars[0] == '-':
        sign, start = -1, 1
    for ch in chars[start:]:
        value = value * 10 + (ord(ch) - 48)
    return sign * value


def solve(a, b):
    return parse(a) + parse(b)


class Solution:
    def addSignedArrays(self, a, b):
        return solve(a, b)
