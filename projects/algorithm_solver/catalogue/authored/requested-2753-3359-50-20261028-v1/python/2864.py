"""Original frontend 2864 variant; qualification unknown."""


def solve(s: str) -> str:
    ones = s.count("1")
    zeros = len(s) - ones
    return "1" * (ones - 1) + "0" * zeros + "1"


maximumOddBinaryNumber = solve


class Solution:
    def maximumOddBinaryNumber(self, s: str) -> str:
        return solve(s)
