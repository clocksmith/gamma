"""1598. Crawler Log Folder (Easy).

Specification: https://leetcode.com/problems/crawler-log-folder/description/
"""


def solve(logs: list[str]) -> int:
    """O(n) time, O(1) auxiliary space; preserve the log."""
    depth = 0
    for operation in logs:
        if operation == '../':
            depth = max(0, depth - 1)
        elif operation != './':
            depth += 1
    return depth


class Solution:
    def minOperations(self, logs: list[str]) -> int:
        return solve(logs)
