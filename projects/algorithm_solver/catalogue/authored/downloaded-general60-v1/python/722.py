"""722. Remove Comments (Medium).

Specification: https://leetcode.com/problems/remove-comments/description/
"""


def solve(source: list[str]) -> list[str]:
    result = []
    in_block = False
    current = ''
    for line in source:
        i = 0
        while i < len(line):
            if not in_block and i + 1 < len(line) and line[i] == '/' and line[i + 1] == '*':
                in_block = True
                i += 2
            elif in_block and i + 1 < len(line) and line[i] == '*' and line[i + 1] == '/':
                in_block = False
                i += 2
            elif not in_block and i + 1 < len(line) and line[i] == '/' and line[i + 1] == '/':
                break
            elif not in_block:
                current += line[i]
                i += 1
            else:
                i += 1
        if not in_block and current != '':
            result.append(current)
            current = ''
    return result


class Solution:
    def removeComments(self, source: list[str]) -> list[str]:
        return solve(source)
