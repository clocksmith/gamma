"""609. Find Duplicate File in System (Medium).

Specification: https://leetcode.com/problems/find-duplicate-file-in-system/description/
"""


def solve(paths: list[str]) -> list[list[str]]:
    groups = {}
    for path in paths:
        parts = path.split(' ')
        directory = parts[0]
        for part in parts[1:]:
            open_index = part.index('(')
            name = part[:open_index]
            content = part[open_index + 1:-1]
            full = directory + '/' + name
            groups.setdefault(content, []).append(full)
    result = []
    for group in groups.values():
        if len(group) > 1:
            result.append(sorted(group))
    result.sort(key=lambda group: group[0])
    return result


class Solution:
    def findDuplicate(self, paths: list[str]) -> list[list[str]]:
        return solve(paths)
