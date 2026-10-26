"""1269. Number of Ways to Stay in the Same Place After Some Steps: bounded-position dynamic programming; O(steps*min(arrLen, steps)) time and O(min(arrLen, steps)) space."""


def solve(steps: int, arrLen: int) -> int:
    modulus = 1_000_000_007
    width = min(arrLen, steps // 2 + 1)
    ways = [0] * width
    ways[0] = 1
    for _ in range(steps):
        following = [0] * width
        for position, count in enumerate(ways):
            following[position] = (following[position] + count) % modulus
            if position:
                following[position - 1] = (following[position - 1] + count) % modulus
            if position + 1 < width:
                following[position + 1] = (following[position + 1] + count) % modulus
        ways = following
    return ways[0]


class Solution:
    def numWays(self, steps: int, arrLen: int) -> int:
        return solve(steps, arrLen)
