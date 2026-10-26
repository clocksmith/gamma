"""762. Prime Number of Set Bits in Binary Representation (Easy).

Specification: https://leetcode.com/problems/prime-number-of-set-bits-in-binary-representation/description/
"""


def solve(left: int, right: int) -> int:
    """O((right - left + 1) * log right) time, O(1) space under the stated range up to 10^6."""
    primes = {2, 3, 5, 7, 11, 13, 17, 19}
    result = 0
    for value in range(left, right + 1):
        remaining = value
        count = 0
        while remaining > 0:
            count += remaining % 2
            remaining //= 2
        if count in primes:
            result += 1
    return result


class Solution:
    def countPrimeSetBits(self, left: int, right: int) -> int:
        return solve(left, right)
