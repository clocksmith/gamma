"""3320. Count the Number of Winning Sequences: rolling dynamic programming over score difference and last move."""


def solve(s: str) -> int:
    """O(n^2) time and O(n) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    n = len(s)
    width = 2 * n + 1
    symbols = {'F': 0, 'W': 1, 'E': 2}
    ways = [[0] * width for _ in range(3)]
    first = symbols[s[0]]
    for move in range(3):
        difference = (move - first) % 3
        delta = 0 if difference == 0 else 1 if difference == 1 else -1
        ways[move][n + delta] = 1
    for round_index in range(1, n):
        opponent = symbols[s[round_index]]
        following = [[0] * width for _ in range(3)]
        for move in range(3):
            difference = (move - opponent) % 3
            delta = 0 if difference == 0 else 1 if difference == 1 else -1
            for previous in range(3):
                if previous == move:
                    continue
                for score in range(n - round_index, n + round_index + 1):
                    following[move][score + delta] = (following[move][score + delta] + ways[previous][score]) % modulus
        ways = following
    return sum(sum(row[n + 1:]) for row in ways) % modulus


class Solution:
    def countWinningSequences(self, s: str) -> int:
        return solve(s)
