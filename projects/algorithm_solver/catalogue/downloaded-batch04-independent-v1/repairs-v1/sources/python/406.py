"""406. Queue Reconstruction by Height (Medium).

Specification: https://leetcode.com/problems/queue-reconstruction-by-height/description/
"""


def solve(people: list[list[int]]) -> list[list[int]]:
    ordered = sorted(people, key=lambda p: (-p[0], p[1]))
    result = []
    for person in ordered:
        result.insert(person[1], person[:])
    return result


class Solution:
    def reconstructQueue(self, people: list[list[int]]) -> list[list[int]]:
        return solve(people)
