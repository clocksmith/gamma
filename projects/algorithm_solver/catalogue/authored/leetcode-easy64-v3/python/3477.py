"""3477. Fruits Into Baskets II (Easy).

Specification: https://leetcode.com/problems/fruits-into-baskets-ii/description/
"""


def solve(fruits: list[int], baskets: list[int]) -> int:
    """O(n^2) time, O(n) space; choose the leftmost available fit and preserve both arrays."""
    used = [False] * len(baskets)
    unplaced = 0
    for quantity in fruits:
        placed = False
        for index, capacity in enumerate(baskets):
            if not used[index] and capacity >= quantity:
                used[index] = True
                placed = True
                break
        if not placed:
            unplaced += 1
    return unplaced


class Solution:
    def numOfUnplacedFruits(self, fruits: list[int], baskets: list[int]) -> int:
        return solve(fruits, baskets)
