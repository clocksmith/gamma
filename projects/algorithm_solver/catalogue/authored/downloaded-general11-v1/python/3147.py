"""3147. Taking Maximum Energy From the Mystic Dungeon (Medium).

Specification: https://leetcode.com/problems/taking-maximum-energy-from-the-mystic-dungeon/description/
"""


def solve(energy: list[int], k: int) -> int:
    n = len(energy)
    dp = list(energy)
    best = None
    for i in range(n - 1, -1, -1):
        if i + k < n:
            dp[i] += dp[i + k]
        if best is None or dp[i] > best:
            best = dp[i]
    return best


class Solution:
    def maximumEnergy(self, energy, k):
        return solve(energy, k)
