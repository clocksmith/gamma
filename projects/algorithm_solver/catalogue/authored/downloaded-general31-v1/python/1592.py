"""1592. Rearrange Spaces Between Words (Easy).

Specification: https://leetcode.com/problems/rearrange-spaces-between-words/description/
"""


def solve(text: str) -> str:
    words = [w for w in text.split(' ') if w]
    spaces = text.count(' ')
    if len(words) == 1:
        return words[0] + ' ' * spaces
    between = spaces // (len(words) - 1)
    trailing = spaces % (len(words) - 1)
    return (' ' * between).join(words) + ' ' * trailing


class Solution:
    def reorderSpaces(self, text: str) -> str:
        return solve(text)
