"""1042. Flower Planting With No Adjacent (Medium).

Specification: https://leetcode.com/problems/flower-planting-with-no-adjacent/description/
"""


def solve(n: int, paths: list[list[int]]) -> list[int]:
    graph = [[] for _ in range(n)]
    for a, b in paths:
        graph[a - 1].append(b - 1)
        graph[b - 1].append(a - 1)
    answer = [0] * n
    for garden in range(n):
        used = set()
        for neighbor in graph[garden]:
            if answer[neighbor] != 0:
                used.add(answer[neighbor])
        for color in range(1, 5):
            if color not in used:
                answer[garden] = color
                break
    return answer


class Solution:
    def gardenNoAdj(self, n: int, paths: list[list[int]]) -> list[int]:
        return solve(n, paths)
