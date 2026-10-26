"""1047. Remove All Adjacent Duplicates In String (Easy).

Specification: https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; cancelling neighboring equal characters maintains the reduced prefix."""
    stack = []
    for character in s:
        if stack and stack[-1] == character:
            stack.pop()
        else:
            stack.append(character)
    return ''.join(stack)


class Solution:
    def removeDuplicates(self, s: str) -> str:
        return solve(s)
