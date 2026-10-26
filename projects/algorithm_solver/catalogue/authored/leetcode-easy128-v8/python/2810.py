"""2810. Faulty Keyboard (Easy).

Specification: https://leetcode.com/problems/faulty-keyboard/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; toggle orientation and postpone reversal until final assembly."""
    left = []
    right = []
    reversed_order = False
    for character in s:
        if character == 'i':
            reversed_order = not reversed_order
        elif reversed_order:
            left.append(character)
        else:
            right.append(character)
    result = left[::-1] + right
    if reversed_order:
        result.reverse()
    return ''.join(result)


class Solution:
    def finalString(self, s: str) -> str:
        return solve(s)
