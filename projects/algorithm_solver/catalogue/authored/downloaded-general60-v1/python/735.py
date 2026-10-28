"""735. Asteroid Collision (Medium).

Specification: https://leetcode.com/problems/asteroid-collision/description/
"""


def solve(asteroids: list[int]) -> list[int]:
    stack = []
    for value in asteroids:
        alive = True
        while alive and value < 0 and stack and stack[-1] > 0:
            top = stack[-1]
            if top < -value:
                stack.pop()
            elif top == -value:
                stack.pop()
                alive = False
            else:
                alive = False
        if alive:
            stack.append(value)
    return stack


class Solution:
    def asteroidCollision(self, asteroids: list[int]) -> list[int]:
        return solve(asteroids)
