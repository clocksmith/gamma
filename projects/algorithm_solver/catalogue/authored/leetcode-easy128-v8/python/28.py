"""28. Find the Index of the First Occurrence in a String (Easy).

Specification: https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/description/
"""


def solve(haystack: str, needle: str) -> int:
    """O(n + m) time, O(m) space; KMP prefix links avoid repeated comparisons."""
    if not needle:
        return 0
    prefix = [0] * len(needle)
    matched = 0
    for index in range(1, len(needle)):
        while matched > 0 and needle[index] != needle[matched]:
            matched = prefix[matched - 1]
        if needle[index] == needle[matched]:
            matched += 1
        prefix[index] = matched
    matched = 0
    for index, character in enumerate(haystack):
        while matched > 0 and character != needle[matched]:
            matched = prefix[matched - 1]
        if character == needle[matched]:
            matched += 1
        if matched == len(needle):
            return index - len(needle) + 1
    return -1


class Solution:
    def strStr(self, haystack: str, needle: str) -> int:
        return solve(haystack, needle)
