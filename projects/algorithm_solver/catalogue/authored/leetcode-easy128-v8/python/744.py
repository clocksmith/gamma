"""744. Find Smallest Letter Greater Than Target (Easy).

Specification: https://leetcode.com/problems/find-smallest-letter-greater-than-target/description/
"""


def solve(letters: list[str], target: str) -> str:
    """O(log n) time, O(1) space; upper-bound search with circular wraparound."""
    left, right = 0, len(letters)
    while left < right:
        middle = left + (right - left) // 2
        if letters[middle] <= target:
            left = middle + 1
        else:
            right = middle
    return letters[left % len(letters)]


class Solution:
    def nextGreatestLetter(self, letters: list[str], target: str) -> str:
        return solve(letters, target)
