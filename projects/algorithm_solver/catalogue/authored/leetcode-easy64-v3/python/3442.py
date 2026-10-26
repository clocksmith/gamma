"""3442. Maximum Difference Between Even and Odd Frequency I (Easy).

Specification: https://leetcode.com/problems/maximum-difference-between-even-and-odd-frequency-i/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) alphabet space; zero frequencies are not eligible even frequencies."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    largest_odd = 0
    smallest_even = float('inf')
    for count in counts:
        if count % 2 == 1:
            largest_odd = max(largest_odd, count)
        elif count > 0:
            smallest_even = min(smallest_even, count)
    return largest_odd - smallest_even


class Solution:
    def maxDifference(self, s: str) -> int:
        return solve(s)
