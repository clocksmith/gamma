"""1725. Number Of Rectangles That Can Form The Largest Square (Easy).

Specification: https://leetcode.com/problems/number-of-rectangles-that-can-form-the-largest-square/description/
"""


def solve(rectangles: list[list[int]]) -> int:
    """O(n) time, O(1) space; the shorter side bounds the square in each rectangle."""
    largest = count = 0
    for length, width in rectangles:
        side = min(length, width)
        if side > largest:
            largest = side
            count = 1
        elif side == largest:
            count += 1
    return count


class Solution:
    def countGoodRectangles(self, rectangles: list[list[int]]) -> int:
        return solve(rectangles)
