"""2053. Kth Distinct String in an Array (Easy).

Specification: https://leetcode.com/problems/kth-distinct-string-in-an-array/description/
"""


def solve(arr: list[str], k: int) -> str:
    """O(total characters) expected time, O(n) map entries; retain original order and preserve arr."""
    counts = {}
    for word in arr:
        counts[word] = counts.get(word, 0) + 1
    remaining = k
    for word in arr:
        if counts[word] != 1:
            continue
        remaining -= 1
        if remaining == 0:
            return word
    return ''


class Solution:
    def kthDistinct(self, arr: list[str], k: int) -> str:
        return solve(arr, k)
