"""Hack2Hire 679dc578996c3c60bd38b5bc (Asteroid Collision - Different Speed) over an INFERRED spec; qualification unknown."""


def solve(masses, speeds):
    stack = []  # indices of survivors so far
    for i in range(len(masses)):
        if speeds[i] > 0:
            stack.append(i)
            continue
        power = masses[i] * -speeds[i]
        alive = True
        while stack and speeds[stack[-1]] > 0:
            other = masses[stack[-1]] * speeds[stack[-1]]
            if other < power:
                stack.pop()
                continue
            if other == power:
                stack.pop()
            alive = False
            break
        if alive:
            stack.append(i)
    return [[masses[i], speeds[i]] for i in stack]


class Solution:
    def asteroidCollision(self, masses, speeds):
        return solve(masses, speeds)
