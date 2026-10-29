# 391 — Perfect Rectangle. Original implementation; authored candidate, not independently qualified.
def solve(rectangles):
    corners, area = set(), 0
    left = bottom = float('inf')
    right = top = float('-inf')
    for x1, y1, x2, y2 in rectangles:
        left, bottom = min(left, x1), min(bottom, y1)
        right, top = max(right, x2), max(top, y2)
        area += (x2 - x1) * (y2 - y1)
        for point in ((x1, y1), (x1, y2), (x2, y1), (x2, y2)):
            if point in corners:
                corners.remove(point)
            else:
                corners.add(point)
    return area == (right - left) * (top - bottom) and corners == {(left, bottom), (left, top), (right, bottom), (right, top)}

isRectangleCover = solve

class Solution:
    isRectangleCover = staticmethod(solve)
