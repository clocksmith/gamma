"""165. Compare Version Numbers (Medium).

Specification: https://leetcode.com/problems/compare-version-numbers/description/
"""


def solve(version1: str, version2: str) -> int:
    parts1 = [int(v) for v in version1.split('.')]
    parts2 = [int(v) for v in version2.split('.')]
    length = max(len(parts1), len(parts2))
    for i in range(length):
        a = parts1[i] if i < len(parts1) else 0
        b = parts2[i] if i < len(parts2) else 0
        if a < b:
            return -1
        if a > b:
            return 1
    return 0


class Solution:
    def compareVersion(self, version1: str, version2: str) -> int:
        return solve(version1, version2)
