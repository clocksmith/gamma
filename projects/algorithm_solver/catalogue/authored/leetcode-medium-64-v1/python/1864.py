"""1864. Minimum Number of Swaps to Make the Binary String Alternating: count mismatches against each frequency-feasible alternating pattern."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    zeros = s.count('0')
    ones = len(s) - zeros
    if abs(zeros - ones) > 1:
        return -1
    mismatch_zero = sum((character == '1') != (index % 2 == 1)
                        for index, character in enumerate(s))
    mismatch_one = len(s) - mismatch_zero
    if zeros > ones:
        return mismatch_zero // 2
    if ones > zeros:
        return mismatch_one // 2
    return min(mismatch_zero, mismatch_one) // 2


class Solution:
    def minSwaps(self, s: str) -> int:
        return solve(s)
