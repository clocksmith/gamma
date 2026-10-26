"""2457. Minimum Addition to Make Integer Beautiful: round upward at successive decimal places until the digit sum fits."""


def solve(n: int, target: int) -> int:
    """O(d^2) time and O(1) auxiliary space for at most 13 decimal digits; inputs are read-only."""
    def digit_sum(value: int) -> int:
        total = 0
        while value:
            total += value % 10
            value //= 10
        return total

    current = n
    place = 10
    while digit_sum(current) > target:
        current = (current + place - 1) // place * place
        place *= 10
    return current - n


class Solution:
    def makeIntegerBeautiful(self, n: int, target: int) -> int:
        return solve(n, target)
