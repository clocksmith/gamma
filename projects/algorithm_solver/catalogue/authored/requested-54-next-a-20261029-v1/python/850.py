"""Original development candidate; qualification unknown."""
def solve(rectangles):
    xs = sorted({x for a,b,c,d in rectangles for x in (a,c)})
    area = 0
    for left,right in zip(xs,xs[1:]):
        intervals = sorted((b,d) for a,b,c,d in rectangles if a <= left < c)
        length = 0
        end = -1
        for bottom,top in intervals:
            length += max(0,top-max(bottom,end))
            end = max(end,top)
        area += (right-left)*length
    return area%1000000007


class Solution:
    def rectangleArea(self, rectangles):
        return solve(rectangles)
