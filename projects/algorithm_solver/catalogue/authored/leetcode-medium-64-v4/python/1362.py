"""1362. Closest Divisors: find the closest factor pair for each of the two permitted products."""
from math import isqrt


def solve(num: int) -> list[int]:
    """O(sqrt(num + 2)) time and O(1) auxiliary space; inputs are read-only."""
    def factors(value: int) -> list[int]:
        divisor = isqrt(value)
        while value % divisor:
            divisor -= 1
        return [divisor, value // divisor]

    first = factors(num + 1)
    second = factors(num + 2)
    return first if first[1] - first[0] <= second[1] - second[0] else second


class Solution:
    def closestDivisors(self, num: int) -> list[int]:
        return solve(num)
