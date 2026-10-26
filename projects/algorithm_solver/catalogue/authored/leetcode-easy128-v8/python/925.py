"""925. Long Pressed Name (Easy).

Specification: https://leetcode.com/problems/long-pressed-name/description/
"""


def solve(name: str, typed: str) -> bool:
    """O(n + m) time, O(1) space; unmatched typed letters must repeat the immediately previous letter."""
    matched = 0
    for index, character in enumerate(typed):
        if matched < len(name) and character == name[matched]:
            matched += 1
        elif index == 0 or character != typed[index - 1]:
            return False
    return matched == len(name)


class Solution:
    def isLongPressedName(self, name: str, typed: str) -> bool:
        return solve(name, typed)
