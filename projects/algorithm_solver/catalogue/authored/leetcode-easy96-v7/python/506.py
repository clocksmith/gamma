"""506. Relative Ranks (Easy).

Specification: https://leetcode.com/problems/relative-ranks/description/
"""


def solve(score: list[int]) -> list[str]:
    """O(n log n) time, O(n) space; rank distinct scores without mutating their original order."""
    order = sorted(range(len(score)), key=lambda index: -score[index])
    medals = ['Gold Medal', 'Silver Medal', 'Bronze Medal']
    result = [''] * len(score)
    for rank, index in enumerate(order):
        result[index] = medals[rank] if rank < 3 else str(rank + 1)
    return result


class Solution:
    def findRelativeRanks(self, score: list[int]) -> list[str]:
        return solve(score)
