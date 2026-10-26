"""1640. Check Array Formation Through Concatenation (Easy).

Specification: https://leetcode.com/problems/check-array-formation-through-concatenation/description/
"""


def solve(arr: list[int], pieces: list[list[int]]) -> bool:
    """O(n) expected time, O(p) space for p pieces; preserve arr, pieces, and their rows."""
    by_first_value = {piece[0]: piece for piece in pieces}
    index = 0
    while index < len(arr):
        piece = by_first_value.get(arr[index])
        if piece is None:
            return False
        for value in piece:
            if index >= len(arr) or arr[index] != value:
                return False
            index += 1
    return True


class Solution:
    def canFormArray(self, arr: list[int], pieces: list[list[int]]) -> bool:
        return solve(arr, pieces)
