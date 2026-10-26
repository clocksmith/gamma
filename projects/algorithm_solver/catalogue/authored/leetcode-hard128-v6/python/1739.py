"""1739. Building Boxes.

Fill complete triangular layers, then extend the last floor row; O(cube_root(n)) time, O(1) space.
"""

def solve(n: int) -> int:
    height = floor = volume = 0
    while volume + floor + height + 1 <= n:
        height += 1
        floor += height
        volume += floor
    extra = 0
    while volume < n:
        extra += 1
        volume += extra
    return floor + extra


class Solution:
    def minimumBoxes(self, n: int) -> int:
        return solve(n)
