"""1422. Maximum Score After Splitting a String (Easy).

Specification: https://leetcode.com/problems/maximum-score-after-splitting-a-string/description/
"""


def solve(s: str) -> int:
    """O(n) time, O(1) auxiliary space; both split parts remain nonempty."""
    right_ones = s.count('1')
    left_zeros = 0
    result = 0
    for index in range(len(s) - 1):
        if s[index] == '0':
            left_zeros += 1
        else:
            right_ones -= 1
        result = max(result, left_zeros + right_ones)
    return result


class Solution:
    def maxScore(self, s: str) -> int:
        return solve(s)
