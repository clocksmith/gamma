"""1987. Number of Unique Good Subsequences."""


def solve(binary: str) -> int:
    """Distinct valid subsequences grouped by final bit; O(n) time and O(1) space. Inputs are preserved."""
    modulus = 1_000_000_007
    ending_zero = 0
    ending_one = 0
    has_zero = 0
    for digit in binary:
        if digit == '1':
            ending_one = (ending_zero + ending_one + 1) % modulus
        else:
            ending_zero = (ending_zero + ending_one) % modulus
            has_zero = 1
    return (ending_zero + ending_one + has_zero) % modulus


class Solution:
    def numberOfUniqueGoodSubsequences(self, binary: str) -> int:
        return solve(binary)
