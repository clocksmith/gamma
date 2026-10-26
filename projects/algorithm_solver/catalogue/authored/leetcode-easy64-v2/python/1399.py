"""1399. Count Largest Group (Easy).

Specification: https://leetcode.com/problems/count-largest-group/description/
"""


def solve(n: int) -> int:
    """O(n * d) time, O(d) space; d is the decimal digit count of n."""
    counts = {}
    largest = 0
    for value in range(1, n + 1):
        remaining = value
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        count = counts.get(digit_sum, 0) + 1
        counts[digit_sum] = count
        largest = max(largest, count)
    return sum(count == largest for count in counts.values())


class Solution:
    def countLargestGroup(self, n: int) -> int:
        return solve(n)
