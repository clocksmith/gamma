class Solution:
    def countGoodRectangles(self, rectangles: list[list[int]]) -> int:
        largest = 0
        count = 0
        for length, width in rectangles:
            side = min(length, width)
            if side > largest:
                largest = side
                count = 1
            elif side == largest:
                count += 1
        return count
