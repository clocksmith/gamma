"""1866. Number of Ways to Rearrange Sticks With K Sticks Visible."""


def solve(n: int, k: int) -> int:
    """Insert the shortest stick into a visibility DP; O(n*k) time and O(k) space. Inputs are preserved."""
    modulus = 1_000_000_007
    ways = [0] * (k + 1)
    ways[0] = 1
    for size in range(1, n + 1):
        following = [0] * (k + 1)
        for visible in range(1, min(size, k) + 1):
            following[visible] = (ways[visible - 1] + (size - 1) * ways[visible]) % modulus
        ways = following
    return ways[k]


class Solution:
    def rearrangeSticks(self, n: int, k: int) -> int:
        return solve(n, k)
