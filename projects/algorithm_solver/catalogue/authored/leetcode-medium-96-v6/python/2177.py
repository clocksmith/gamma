"""2177. Find Three Consecutive Integers That Sum to a Given Number: use the integer average as the unique middle value."""


def solve(num: int) -> list[int]:
    """O(1) time and O(1) result space on the bounded integer domain; inputs are read-only."""
    if num % 3:
        return []
    middle = num // 3
    return [middle - 1, middle, middle + 1]


class Solution:
    def sumOfThree(self, num: int) -> list[int]:
        return solve(num)
