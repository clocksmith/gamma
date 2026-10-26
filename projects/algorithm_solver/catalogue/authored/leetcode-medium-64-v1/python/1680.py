"""1680. Concatenation of Consecutive Binary Numbers: append each integer using its current binary place multiplier."""


def solve(n: int) -> int:
    """O(n) time and O(1) auxiliary space under n <= 100000; inputs are read-only."""
    modulus = 1_000_000_007
    multiplier = 1
    answer = 0
    for value in range(1, n + 1):
        if value & (value - 1) == 0:
            multiplier *= 2
        answer = (answer * multiplier + value) % modulus
    return answer


class Solution:
    def concatenatedBinary(self, n: int) -> int:
        return solve(n)
