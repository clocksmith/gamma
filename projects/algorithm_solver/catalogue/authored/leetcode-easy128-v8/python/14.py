"""14. Longest Common Prefix (Easy).

Specification: https://leetcode.com/problems/longest-common-prefix/description/
"""


def solve(strs: list[str]) -> str:
    """O(n * m) time, O(1) auxiliary space excluding the result; compare a shared prefix."""
    length = len(strs[0])
    for index in range(1, len(strs)):
        length = min(length, len(strs[index]))
        matched = 0
        while matched < length and strs[index][matched] == strs[0][matched]:
            matched += 1
        length = matched
        if length == 0:
            break
    return strs[0][:length]


class Solution:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        return solve(strs)
