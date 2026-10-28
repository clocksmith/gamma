"""768. Max Chunks To Make Sorted II (Medium).

Specification: https://leetcode.com/problems/max-chunks-to-make-sorted-ii/description/
"""


def solve(arr: list[int]) -> int:
    ordered = sorted(arr)
    chunks = 0
    for i in range(len(arr)):
        if sorted(arr[:i + 1]) == ordered[:i + 1]:
            chunks += 1
    return chunks


class Solution:
    def maxChunksToSorted(self, arr: list[int]) -> int:
        return solve(arr)
