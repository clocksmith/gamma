"""2379. Minimum Recolors to Get K Consecutive Black Blocks (Easy).

Specification: https://leetcode.com/problems/minimum-recolors-to-get-k-consecutive-black-blocks/description/
"""


def solve(blocks: str, k: int) -> int:
    """O(n) time, O(1) space; minimize white blocks in a k-wide sliding window."""
    whites = 0
    for index in range(k):
        if blocks[index] == 'W':
            whites += 1
    best = whites
    for index in range(k, len(blocks)):
        if blocks[index] == 'W':
            whites += 1
        if blocks[index - k] == 'W':
            whites -= 1
        best = min(best, whites)
    return best


class Solution:
    def minimumRecolors(self, blocks: str, k: int) -> int:
        return solve(blocks, k)
