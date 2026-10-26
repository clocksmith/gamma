"""1736. Latest Time by Replacing Hidden Digits (Easy).

Specification: https://leetcode.com/problems/latest-time-by-replacing-hidden-digits/description/
"""


def solve(time: str) -> str:
    """O(1) time and space for the fixed five-character 24-hour time."""
    result = list(time)
    if result[0] == '?':
        result[0] = '2' if result[1] == '?' or result[1] <= '3' else '1'
    if result[1] == '?':
        result[1] = '3' if result[0] == '2' else '9'
    if result[3] == '?':
        result[3] = '5'
    if result[4] == '?':
        result[4] = '9'
    return ''.join(result)


class Solution:
    def maximumTime(self, time: str) -> str:
        return solve(time)
