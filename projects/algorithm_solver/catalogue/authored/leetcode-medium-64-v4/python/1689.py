"""1689. Partitioning Into Minimum Number Of Deci-Binary Numbers: use the largest decimal digit as the necessary and sufficient layer count."""


def solve(n: str) -> int:
    """O(d) time and O(1) auxiliary space, where d is the number of digits; inputs are read-only."""
    largest = 0
    for digit in n:
        largest = max(largest, ord(digit) - ord('0'))
        if largest == 9:
            return largest
    return largest


class Solution:
    def minPartitions(self, n: str) -> int:
        return solve(n)
