"""1227. Airplane Seat Assignment Probability (Medium).

Specification: https://leetcode.com/problems/airplane-seat-assignment-probability/description/
"""


def solve(n: int) -> float:
    return 1.0 if n == 1 else 0.5


class Solution:
    def nthPersonGetsNthSeat(self, n: int) -> float:
        return solve(n)
