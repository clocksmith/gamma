"""2788. Split Strings by Separator (Easy).

Specification: https://leetcode.com/problems/split-strings-by-separator/description/
"""


def solve(words: list[str], separator: str) -> list[str]:
    """O(total characters) time and space; preserve input order and omit empty pieces."""
    result = []
    for word in words:
        for part in word.split(separator):
            if part:
                result.append(part)
    return result


class Solution:
    def splitWordsBySeparator(self, words: list[str], separator: str) -> list[str]:
        return solve(words, separator)
