"""1935. Maximum Number of Words You Can Type (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-words-you-can-type/description/
"""


def solve(text: str, brokenLetters: str) -> int:
    """O(text length + brokenLetters length) time, O(1) alphabet space; do not allocate word substrings."""
    broken = set(brokenLetters)
    result = 0
    blocked = False
    for index in range(len(text) + 1):
        if index == len(text) or text[index] == ' ':
            if not blocked:
                result += 1
            blocked = False
        elif text[index] in broken:
            blocked = True
    return result


class Solution:
    def canBeTypedWords(self, text: str, brokenLetters: str) -> int:
        return solve(text, brokenLetters)
