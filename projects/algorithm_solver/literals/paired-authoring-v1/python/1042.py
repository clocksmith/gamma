class Solution:
    def gardenNoAdj(self, n: int, paths: list[list[int]]) -> list[int]:
        neighbors = [[] for _ in range(n)]
        for first, second in paths:
            neighbors[first - 1].append(second - 1)
            neighbors[second - 1].append(first - 1)
        colors = [0] * n
        for garden in range(n):
            used = [False] * 5
            for neighbor in neighbors[garden]:
                used[colors[neighbor]] = True
            for color in range(1, 5):
                if not used[color]:
                    colors[garden] = color
                    break
        return colors
