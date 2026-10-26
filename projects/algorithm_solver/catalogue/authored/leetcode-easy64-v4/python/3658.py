"""3658. GCD of Odd and Even Sums (Easy).

Specification: https://leetcode.com/problems/gcd-of-odd-and-even-sums/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; gcd(n*n, n*(n+1)) = n."""
    return n


class Solution:
    def gcdOfOddEvenSums(self, n: int) -> int:
        return solve(n)
