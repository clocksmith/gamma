"""2318. Number of Distinct Roll Sequences: rolling dynamic programming over the previous two die faces."""

from math import gcd


def solve(n: int) -> int:
    """O(6^3 * n) time and O(6^2) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    allowed = [[] for _ in range(7)]
    for previous in range(1, 7):
        allowed[previous] = [face for face in range(1, 7) if face != previous and gcd(face, previous) == 1]
    states = [[0] * 7 for _ in range(7)]
    for face in range(1, 7):
        states[0][face] = 1
    for _ in range(1, n):
        following = [[0] * 7 for _ in range(7)]
        for earlier in range(7):
            for previous in range(1, 7):
                count = states[earlier][previous]
                if count == 0:
                    continue
                for face in allowed[previous]:
                    if face != earlier:
                        following[previous][face] = (following[previous][face] + count) % modulus
        states = following
    return sum(map(sum, states)) % modulus


class Solution:
    def distinctSequences(self, n: int) -> int:
        return solve(n)
