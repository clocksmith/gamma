"""478. Generate Random Point in a Circle."""

from math import cos, sin, sqrt, tau
from random import random


class Solution:
    def __init__(self, radius: float, x_center: float, y_center: float):
        self.radius = radius
        self.x = x_center
        self.y = y_center

    def randPoint(self) -> list[float]:
        angle = tau * random()
        distance = self.radius * sqrt(random())
        return [self.x + distance * cos(angle), self.y + distance * sin(angle)]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
