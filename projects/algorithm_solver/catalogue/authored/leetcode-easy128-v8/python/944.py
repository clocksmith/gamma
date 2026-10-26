"""944. Delete Columns to Make Sorted (Easy).

Specification: https://leetcode.com/problems/delete-columns-to-make-sorted/description/
"""


def solve(strs: list[str]) -> int:
    """O(rows * columns) time, O(1) space; count columns containing a descending adjacent pair."""
    deletions = 0
    for column in range(len(strs[0])):
        for row in range(1, len(strs)):
            if strs[row][column] < strs[row - 1][column]:
                deletions += 1
                break
    return deletions


class Solution:
    def minDeletionSize(self, strs: list[str]) -> int:
        return solve(strs)
