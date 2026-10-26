"""1678. Goal Parser Interpretation (Easy).

Specification: https://leetcode.com/problems/goal-parser-interpretation/description/
"""


def solve(command: str) -> str:
    """O(n) time, O(n) space; command consists of G, (), and (al) tokens."""
    result = []
    index = 0
    while index < len(command):
        if command[index] == 'G':
            result.append('G')
            index += 1
        elif command[index + 1] == ')':
            result.append('o')
            index += 2
        else:
            result.append('al')
            index += 4
    return ''.join(result)


class Solution:
    def interpret(self, command: str) -> str:
        return solve(command)
