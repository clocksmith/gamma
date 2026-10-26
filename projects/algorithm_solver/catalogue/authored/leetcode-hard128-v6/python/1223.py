"""1223. Dice Roll Simulation.

Track the final face and its run length; O(n * sum(rollMax)) time and O(sum(rollMax)) space. Inputs are preserved.
"""

def solve(n: int, rollMax: list[int]) -> int:
    modulus = 1_000_000_007
    runs = [[0] * (limit + 1) for limit in rollMax]
    for face in range(6):
        runs[face][1] = 1
    for _ in range(1, n):
        totals = [sum(row) % modulus for row in runs]
        total = sum(totals) % modulus
        following = [[0] * (limit + 1) for limit in rollMax]
        for face, limit in enumerate(rollMax):
            following[face][1] = (total - totals[face]) % modulus
            for length in range(2, limit + 1):
                following[face][length] = runs[face][length - 1]
        runs = following
    return sum(map(sum, runs)) % modulus


class Solution:
    def dieSimulator(self, n: int, rollMax: list[int]) -> int:
        return solve(n, rollMax)
