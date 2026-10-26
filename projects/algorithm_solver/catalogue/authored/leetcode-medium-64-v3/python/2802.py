"""2802. Find The K-th Lucky Number: map the successor binary digits to four and seven."""


def solve(k: int) -> str:
    """O(log(k + 1)) time and output space; inputs are read-only."""
    return ''.join('4' if bit == '0' else '7' for bit in bin(k + 1)[3:])


class Solution:
    def kthLuckyNumber(self, k: int) -> str:
        return solve(k)
