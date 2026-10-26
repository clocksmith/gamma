"""3114. Latest Time You Can Obtain After Replacing Characters (Easy).

Specification: https://leetcode.com/problems/latest-time-you-can-obtain-after-replacing-characters/description/
"""


def solve(s: str) -> str:
    """O(1) time and space; the hour range is 00 through 11, not 00 through 23."""
    time = list(s)
    if time[0] == '?':
        time[0] = '1' if time[1] == '?' or time[1] <= '1' else '0'
    if time[1] == '?':
        time[1] = '1' if time[0] == '1' else '9'
    if time[3] == '?':
        time[3] = '5'
    if time[4] == '?':
        time[4] = '9'
    return ''.join(time)


class Solution:
    def findLatestTime(self, s: str) -> str:
        return solve(s)
