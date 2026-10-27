"""391. Perfect Rectangle. Compare total area and odd-multiplicity corners using exact integers."""

def solve(rectangles: list[list[int]]) -> bool:
    if not rectangles:
        return False
    corners = set()
    area = 0
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    for x1, y1, x2, y2 in rectangles:
        area += (x2 - x1) * (y2 - y1)
        min_x, min_y = min(min_x, x1), min(min_y, y1)
        max_x, max_y = max(max_x, x2), max(max_y, y2)
        for point in ((x1, y1), (x1, y2), (x2, y1), (x2, y2)):
            if point in corners:
                corners.remove(point)
            else:
                corners.add(point)
    return (area == (max_x - min_x) * (max_y - min_y)
            and corners == {(min_x, min_y), (min_x, max_y),
                            (max_x, min_y), (max_x, max_y)})


class Solution:
    def isRectangleCover(self, rectangles: list[list[int]]) -> bool:
        return solve(rectangles)
