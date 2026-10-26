"""660. Remove 9: base-nine digits interpreted as decimal digits."""


def solve(n: int) -> int:
    """O(log n) time and O(1) auxiliary space. Inputs are preserved."""
    answer = 0
    place = 1
    remaining = n
    while remaining:
        remaining, digit = divmod(remaining, 9)
        answer += digit * place
        place *= 10
    return answer


class Solution:
    def newInteger(self, n: int) -> int:
        return solve(n)
