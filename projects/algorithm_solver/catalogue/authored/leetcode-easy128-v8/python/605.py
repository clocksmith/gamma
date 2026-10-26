"""605. Can Place Flowers (Easy).

Specification: https://leetcode.com/problems/can-place-flowers/description/
"""


def solve(flowerbed: list[int], n: int) -> bool:
    """O(m) time, O(1) space; greedily plant using virtual previous occupancy; preserve flowerbed."""
    remaining = n
    previous = 0
    for index, occupied in enumerate(flowerbed):
        if remaining <= 0:
            return True
        following = flowerbed[index + 1] if index + 1 < len(flowerbed) else 0
        if occupied == 0 and previous == 0 and following == 0:
            remaining -= 1
            previous = 1
        else:
            previous = occupied
    return remaining <= 0


class Solution:
    def canPlaceFlowers(self, flowerbed: list[int], n: int) -> bool:
        return solve(flowerbed, n)
