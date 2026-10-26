"""1465. Maximum Area of a Piece of Cake After Horizontal and Vertical Cuts: multiply the largest gaps including both cake boundaries."""


def solve(h: int, w: int, horizontalCuts: list[int], verticalCuts: list[int]) -> int:
    """O(a log a + b log b) time and O(a + b) space for a horizontal and b vertical cuts; inputs are read-only."""
    def largest_gap(length: int, cuts: list[int]) -> int:
        previous = best = 0
        for cut in sorted(cuts):
            best = max(best, cut - previous)
            previous = cut
        return max(best, length - previous)

    height = largest_gap(h, horizontalCuts)
    width = largest_gap(w, verticalCuts)
    return height * width % 1_000_000_007


class Solution:
    def maxArea(self, h: int, w: int, horizontalCuts: list[int], verticalCuts: list[int]) -> int:
        return solve(h, w, horizontalCuts, verticalCuts)
