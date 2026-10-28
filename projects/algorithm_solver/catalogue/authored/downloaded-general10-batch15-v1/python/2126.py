"""2126. Destroying Asteroids (Medium).

Specification: https://leetcode.com/problems/destroying-asteroids/description/
"""


def solve(mass: int, asteroids: list[int]) -> bool:
    for asteroid in sorted(asteroids):
        if mass < asteroid:
            return False
        mass += asteroid
    return True


class Solution:
    def asteroidsDestroyed(self, mass: int, asteroids: list[int]) -> bool:
        return solve(mass, asteroids)
