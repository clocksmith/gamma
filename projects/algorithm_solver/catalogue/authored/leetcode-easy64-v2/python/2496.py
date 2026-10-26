"""2496. Maximum Value of a String in an Array (Easy).

Specification: https://leetcode.com/problems/maximum-value-of-a-string-in-an-array/description/
"""


def solve(strs: list[str]) -> int:
    """O(total characters) time, O(1) auxiliary space; strings contain at most nine characters."""
    result = 0
    for text in strs:
        value = 0
        for character in text:
            if not ('0' <= character <= '9'):
                value = len(text)
                break
            value = value * 10 + ord(character) - ord('0')
        result = max(result, value)
    return result


class Solution:
    def maximumValue(self, strs: list[str]) -> int:
        return solve(strs)
