"""1776. Car Fleet II."""


def solve(cars: list[list[int]]) -> list[float]:
    """Monotonic stack of future fleets; O(n) time and O(n) space. Inputs are preserved."""
    answer = [-1.0] * len(cars)
    stack = []
    for index in range(len(cars) - 1, -1, -1):
        position, speed = cars[index]
        while stack:
            front = stack[-1]
            next_position, next_speed = cars[front]
            if speed <= next_speed:
                stack.pop()
                continue
            collision = (next_position - position) / (speed - next_speed)
            if answer[front] < 0 or collision <= answer[front]:
                answer[index] = collision
                break
            stack.pop()
        stack.append(index)
    return answer


class Solution:
    def getCollisionTimes(self, cars: list[list[int]]) -> list[float]:
        return solve(cars)
