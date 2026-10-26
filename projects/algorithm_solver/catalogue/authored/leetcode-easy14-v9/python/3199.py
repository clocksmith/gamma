"""3199. Count Triplets with Even XOR Set Bits I (Easy).

Specification: https://leetcode.com/problems/count-triplets-with-even-xor-set-bits-i/description/
"""


def solve(a: list[int], b: list[int], c: list[int]) -> int:
    """O(n + m + k) time, O(1) space for values in [0, 100]; combine popcount-parity counts."""
    def parity_counts(values):
        counts = [0, 0]
        for value in values:
            remaining = value
            parity = 0
            while remaining > 0:
                parity ^= remaining & 1
                remaining >>= 1
            counts[parity] += 1
        return counts

    first = parity_counts(a)
    second = parity_counts(b)
    third = parity_counts(c)
    even_pairs = first[0] * second[0] + first[1] * second[1]
    odd_pairs = first[0] * second[1] + first[1] * second[0]
    return even_pairs * third[0] + odd_pairs * third[1]


class Solution:
    def tripletCount(self, a: list[int], b: list[int], c: list[int]) -> int:
        return solve(a, b, c)
