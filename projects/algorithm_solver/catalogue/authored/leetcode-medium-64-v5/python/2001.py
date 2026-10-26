"""2001. Number of Pairs of Interchangeable Rectangles: count matching reduced integer width-to-height ratios."""
from math import gcd


def solve(rectangles: list[list[int]]) -> int:
    """O(n * log(M + 1)) expected time and O(n) auxiliary space, with M the largest dimension; inputs are read-only."""
    counts = {}
    result = 0
    for width, height in rectangles:
        divisor = gcd(width, height)
        key = (width // divisor, height // divisor)
        previous = counts.get(key, 0)
        result += previous
        counts[key] = previous + 1
    return result


class Solution:
    def interchangeableRectangles(self, rectangles: list[list[int]]) -> int:
        return solve(rectangles)
