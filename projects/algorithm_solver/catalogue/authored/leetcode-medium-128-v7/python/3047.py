"""3047. Find the Largest Area of Square Inside Two Rectangles: inspect each rectangle intersection and take its smaller positive dimension."""


def solve(bottomLeft: list[list[int]], topRight: list[list[int]]) -> int:
    """O(n * n) time and O(1) auxiliary space; inputs are read-only."""
    best = 0
    for left in range(len(bottomLeft)):
        for right in range(left + 1, len(bottomLeft)):
            width = min(topRight[left][0], topRight[right][0]) - max(bottomLeft[left][0], bottomLeft[right][0])
            height = min(topRight[left][1], topRight[right][1]) - max(bottomLeft[left][1], bottomLeft[right][1])
            side = min(width, height)
            if side > 0:
                best = max(best, side * side)
    return best


class Solution:
    def largestSquareArea(self, bottomLeft: list[list[int]], topRight: list[list[int]]) -> int:
        return solve(bottomLeft, topRight)
