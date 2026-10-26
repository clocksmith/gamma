"""3545. Minimum Deletions for At Most K Distinct Characters (Easy).

Specification: https://leetcode.com/problems/minimum-deletions-for-at-most-k-distinct-characters/description/
"""


def solve(s: str, k: int) -> int:
    """O(n) time, O(1) alphabet space; preserve s."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    counts.sort(reverse=True)
    deletions = 0
    for index in range(k, len(counts)):
        deletions += counts[index]
    return deletions


class Solution:
    def minDeletion(self, s: str, k: int) -> int:
        return solve(s, k)
