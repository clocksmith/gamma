"""1499. Max Value of Equation: monotonic deque for y-x inside the x-distance window; O(n) time and O(n) space."""

from collections import deque


def solve(points: list[list[int]], k: int) -> int:
    queue = deque()
    answer = float('-inf')
    for index, (x, y) in enumerate(points):
        while queue and x - points[queue[0]][0] > k:
            queue.popleft()
        if queue:
            previous_x, previous_y = points[queue[0]]
            answer = max(answer, x + y + previous_y - previous_x)
        value = y - x
        while queue and points[queue[-1]][1] - points[queue[-1]][0] <= value:
            queue.pop()
        queue.append(index)
    return answer


class Solution:
    def findMaxValueOfEquation(self, points: list[list[int]], k: int) -> int:
        return solve(points, k)
