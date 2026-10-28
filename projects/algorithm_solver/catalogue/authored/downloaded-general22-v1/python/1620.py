"""1620. Coordinate With Maximum Network Quality (Medium).

Specification: https://leetcode.com/problems/coordinate-with-maximum-network-quality/description/
"""


import math


def solve(towers: list[list[int]], radius: int) -> list[int]:
    best_quality = -1
    best_x = 0
    best_y = 0
    for x in range(51):
        for y in range(51):
            quality = 0
            for tx, ty, q in towers:
                distance = math.sqrt((x - tx) ** 2 + (y - ty) ** 2)
                if distance <= radius:
                    quality += math.floor(q / (1 + distance))
            if quality > best_quality:
                best_quality = quality
                best_x = x
                best_y = y
    return [best_x, best_y]


class Solution:
    def bestCoordinate(self, towers: list[list[int]], radius: int) -> list[int]:
        return solve(towers, radius)
