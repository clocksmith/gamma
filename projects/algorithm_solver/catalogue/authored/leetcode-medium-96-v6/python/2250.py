"""2250. Count Number of Rectangles Containing Each Point: group rectangle widths by the bounded height and binary search qualifying widths."""
from bisect import bisect_left


def solve(rectangles: list[list[int]], points: list[list[int]]) -> list[int]:
    """O(n log n + q H log(n + 1)) time and O(n + q + H) space with H = 100; inputs are read-only."""
    widths = [[] for _ in range(101)]
    for width, height in rectangles:
        widths[height].append(width)
    for group in widths:
        group.sort()
    result = []
    for x, y in points:
        count = 0
        for height in range(y, 101):
            count += len(widths[height]) - bisect_left(widths[height], x)
        result.append(count)
    return result


class Solution:
    def countRectangles(self, rectangles: list[list[int]], points: list[list[int]]) -> list[int]:
        return solve(rectangles, points)
