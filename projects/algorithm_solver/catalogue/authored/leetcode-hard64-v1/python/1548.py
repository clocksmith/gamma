"""1548. The Most Similar Path in a Graph: backward path dynamic programming and deterministic reconstruction."""


def solve(n: int, roads: list[list[int]], names: list[str], targetPath: list[str]) -> list[int]:
    """O(L * (n + E)) time and O(L * n + E) space. Inputs are preserved."""
    adjacency = [[] for _ in range(n)]
    for first, second in roads:
        adjacency[first].append(second)
        adjacency[second].append(first)
    length = len(targetPath)
    if length == 0:
        return []
    choices = [[-1] * n for _ in range(length)]
    cost = [int(name != targetPath[-1]) for name in names]
    for position in range(length - 2, -1, -1):
        following = [length + 1] * n
        for node in range(n):
            best_node = -1
            best_cost = length + 1
            for neighbor in adjacency[node]:
                if cost[neighbor] < best_cost or (cost[neighbor] == best_cost and neighbor < best_node):
                    best_node = neighbor
                    best_cost = cost[neighbor]
            if best_node >= 0:
                following[node] = best_cost + (names[node] != targetPath[position])
                choices[position][node] = best_node
        cost = following
    current = min(range(n), key=lambda node: (cost[node], node))
    if cost[current] > length:
        return []
    answer = [current]
    for position in range(length - 1):
        current = choices[position][current]
        answer.append(current)
    return answer


class Solution:
    def mostSimilar(self, n: int, roads: list[list[int]], names: list[str], targetPath: list[str]) -> list[int]:
        return solve(n, roads, names, targetPath)
