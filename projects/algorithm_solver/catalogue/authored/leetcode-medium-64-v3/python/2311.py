"""2311. Longest Binary Subsequence Less Than or Equal to K: keep every zero and greedily admit low-significance ones from the right."""


def solve(s: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    length = value = 0
    weight = 1
    for char in reversed(s):
        if char == '0' or value + weight <= k:
            if char == '1':
                value += weight
            length += 1
            weight = min(k + 1, weight * 2)
    return length


class Solution:
    def longestSubsequence(self, s: str, k: int) -> int:
        return solve(s, k)
