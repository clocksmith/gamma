"""223. Rectangle Area."""
def solve(ax1: int, ay1: int, ax2: int, ay2: int,
          bx1: int, by1: int, bx2: int, by2: int) -> int:
    overlap_width = max(0, min(ax2, bx2) - max(ax1, bx1))
    overlap_height = max(0, min(ay2, by2) - max(ay1, by1))
    return (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - overlap_width * overlap_height

class Solution:
    def computeArea(self, ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
        return solve(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2)
