"""3258. Count Substrings That Satisfy K-Constraint I (Easy).

Specification: https://leetcode.com/problems/count-substrings-that-satisfy-k-constraint-i/description/
"""


def solve(s: str, k: int) -> int:
    """O(n) time, O(1) auxiliary space; a window is invalid only when both counts exceed k."""
    zeros = 0
    ones = 0
    left = 0
    total = 0
    for right, character in enumerate(s):
        if character == '0':
            zeros += 1
        else:
            ones += 1
        while zeros > k and ones > k:
            if s[left] == '0':
                zeros -= 1
            else:
                ones -= 1
            left += 1
        total += right - left + 1
    return total


class Solution:
    def countKConstraintSubstrings(self, s: str, k: int) -> int:
        return solve(s, k)
