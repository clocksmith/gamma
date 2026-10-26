"""2937. Make Three Strings Equal (Easy).

Specification: https://leetcode.com/problems/make-three-strings-equal/description/
"""


def solve(s1: str, s2: str, s3: str) -> int:
    """O(minimum string length) time, O(1) auxiliary space; preserve all strings."""
    limit = min(len(s1), len(s2), len(s3))
    common = 0
    while common < limit and s1[common] == s2[common] == s3[common]:
        common += 1
    if common == 0:
        return -1
    return len(s1) + len(s2) + len(s3) - 3 * common


class Solution:
    def findMinimumOperations(self, s1: str, s2: str, s3: str) -> int:
        return solve(s1, s2, s3)
