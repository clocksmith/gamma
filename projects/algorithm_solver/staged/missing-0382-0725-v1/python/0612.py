"""612. Shortest Distance in a Plane. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. point2d: x, y (unique integer-coordinate pairs). Output: shortest, rounded to two decimal places; no pair yields NULL."""

from decimal import Decimal, ROUND_HALF_UP, localcontext

def solve(point2d):
    best = None
    for i, first in enumerate(point2d):
        for second in point2d[i + 1:]:
            distance = (first['x'] - second['x']) ** 2 + (first['y'] - second['y']) ** 2
            if best is None or distance < best:
                best = distance
    if best is None:
        return [{'shortest': None}]
    with localcontext() as context:
        context.prec = 60
        value = Decimal(best).sqrt().quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return [{'shortest': float(value)}]


class Solution:
    def shortestDistance(self, point2d):
        return solve(point2d)
