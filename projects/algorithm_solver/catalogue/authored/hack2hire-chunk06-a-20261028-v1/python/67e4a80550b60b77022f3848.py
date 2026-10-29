"""Hack2Hire 67e4a80550b60b77022f3848 (Find Middle Course, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(pairs):
    following, courses = {}, set()
    for prerequisite, course in pairs:
        following[prerequisite] = course
        courses.add(course)
    current = next(p for p, _ in pairs if p not in courses)
    for _ in range(len(pairs) // 2):
        current = following[current]
    return current


class Solution:
    def findMiddleCourse(self, pairs):
        return solve(pairs)
