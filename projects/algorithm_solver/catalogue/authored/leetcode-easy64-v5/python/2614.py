"""2614. Prime In Diagonal (Easy).

Specification: https://leetcode.com/problems/prime-in-diagonal/description/
"""


def solve(nums: list[list[int]]) -> int:
    """O(n * sqrt(M)) time, O(1) auxiliary space; preserve the matrix."""
    def is_prime(value: int) -> bool:
        if value < 2:
            return False
        if value % 2 == 0:
            return value == 2
        divisor = 3
        while divisor * divisor <= value:
            if value % divisor == 0:
                return False
            divisor += 2
        return True

    largest = 0
    size = len(nums)
    for row in range(size):
        primary = nums[row][row]
        secondary = nums[row][size - row - 1]
        if primary > largest and is_prime(primary):
            largest = primary
        if secondary > largest and is_prime(secondary):
            largest = secondary
    return largest


class Solution:
    def diagonalPrime(self, nums: list[list[int]]) -> int:
        return solve(nums)
