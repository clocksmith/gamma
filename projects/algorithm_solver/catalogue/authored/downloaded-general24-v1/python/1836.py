"""1836. Remove Sub-Folders from the Filesystem (Medium).

Specification: https://leetcode.com/problems/remove-sub-folders-from-the-filesystem/description/
"""


def solve(folder: list[str]) -> list[str]:
    ordered = sorted(folder)
    result = []
    for path in ordered:
        if not result or not path.startswith(result[-1] + '/'):
            result.append(path)
    return result


class Solution:
    def removeSubfolders(self, folder: list[str]) -> list[str]:
        return solve(folder)
