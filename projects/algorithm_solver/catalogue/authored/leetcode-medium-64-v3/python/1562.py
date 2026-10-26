"""1562. Find Latest Group of Size M: merge adjacent one-runs using their boundary lengths."""


def solve(arr: list[int], m: int) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    lengths = [0] * (len(arr) + 2)
    groups = 0
    latest = -1
    for step, position in enumerate(arr, 1):
        left = lengths[position - 1]
        right = lengths[position + 1]
        groups -= int(left == m) + int(right == m)
        merged = left + right + 1
        lengths[position - left] = merged
        lengths[position + right] = merged
        groups += int(merged == m)
        if groups:
            latest = step
    return latest


class Solution:
    def findLatestStep(self, arr: list[int], m: int) -> int:
        return solve(arr, m)
