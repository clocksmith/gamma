"""2652. Sum Multiples (Easy).

Specification: https://leetcode.com/problems/sum-multiples/description/
"""


def solve(n: int) -> int:
    """O(1) time and space; inclusion-exclusion over multiples of 3, 5, and 7."""
    def sum_divisible(divisor: int) -> int:
        count = n // divisor
        return divisor * count * (count + 1) // 2

    return (sum_divisible(3) + sum_divisible(5) + sum_divisible(7)
            - sum_divisible(15) - sum_divisible(21) - sum_divisible(35)
            + sum_divisible(105))


class Solution:
    def sumOfMultiples(self, n: int) -> int:
        return solve(n)
