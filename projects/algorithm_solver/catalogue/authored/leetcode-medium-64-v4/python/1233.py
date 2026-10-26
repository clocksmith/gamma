"""1233. Remove Sub-Folders from the Filesystem: sort a copy and reject paths inside the last retained parent."""


def solve(folder: list[str]) -> list[str]:
    """O(n * L * log(n + 1)) time and O(n + L) auxiliary space, where L is maximum path length; inputs are read-only."""
    result = []
    for path in sorted(folder):
        if not result or not path.startswith(result[-1] + '/'):
            result.append(path)
    return result


class Solution:
    def removeSubfolders(self, folder: list[str]) -> list[str]:
        return solve(folder)
