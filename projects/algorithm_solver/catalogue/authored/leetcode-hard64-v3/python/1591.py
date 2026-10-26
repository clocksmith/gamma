"""1591. Strange Printer II: bounding-rectangle dependency graph; O(colors*rows*columns) time and O(colors^2) auxiliary space."""

from collections import deque


def solve(targetGrid: list[list[int]]) -> bool:
    bounds = {}
    for row, values in enumerate(targetGrid):
        for column, color in enumerate(values):
            box = bounds.setdefault(color, [row, row, column, column])
            box[0], box[1] = min(box[0], row), max(box[1], row)
            box[2], box[3] = min(box[2], column), max(box[3], column)
    following = {color: set() for color in bounds}
    indegree = {color: 0 for color in bounds}
    for color, (top, bottom, left, right) in bounds.items():
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                other = targetGrid[row][column]
                if other != color and other not in following[color]:
                    following[color].add(other)
                    indegree[other] += 1
    queue = deque(color for color, degree in indegree.items() if degree == 0)
    count = 0
    while queue:
        color = queue.popleft()
        count += 1
        for other in following[color]:
            indegree[other] -= 1
            if indegree[other] == 0:
                queue.append(other)
    return count == len(bounds)


class Solution:
    def isPrintable(self, targetGrid: list[list[int]]) -> bool:
        return solve(targetGrid)
