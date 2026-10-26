"""552. Student Attendance Record II: six-state attendance dynamic programming."""


def solve(n: int) -> int:
    """O(n) time and O(1) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    states = [[1, 0, 0], [0, 0, 0]]
    for _ in range(n):
        following = [[0, 0, 0], [0, 0, 0]]
        for absent in range(2):
            for late in range(3):
                count = states[absent][late]
                following[absent][0] = (following[absent][0] + count) % modulus
                if absent == 0:
                    following[1][0] = (following[1][0] + count) % modulus
                if late < 2:
                    following[absent][late + 1] = (following[absent][late + 1] + count) % modulus
        states = following
    return sum(map(sum, states)) % modulus


class Solution:
    def checkRecord(self, n: int) -> int:
        return solve(n)
