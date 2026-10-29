"""Hack2Hire 68dd8441fb98b196fa54054b (Build Smallest Number, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(digits):
    count = [0] * 10
    for d in digits:
        count[d] += 1
    first = 1
    while first < 10 and count[first] == 0:
        first += 1
    if first == 10:
        return '0'
    count[first] -= 1
    return str(first) + ''.join(str(d) * count[d] for d in range(10))


class Solution:
    def smallestNumber(self, digits):
        return solve(digits)
