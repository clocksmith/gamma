"""3311. Construct 2D Grid Matching Graph Layout: derive grid coordinates from distances to adjacent corners."""


def solve(n: int, edges: list[list[int]]) -> list[list[int]]:
    """O(n + E) time and O(n + E) space under the rectangular-grid promise. Inputs are preserved."""
    if n == 1:
        return [[0]]
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    corner = min(range(n), key=lambda node: (len(graph[node]), node))

    def distances(start):
        distance = [-1] * n
        distance[start] = 0
        queue = [start]
        for node in queue:
            for neighbor in graph[node]:
                if distance[neighbor] == -1:
                    distance[neighbor] = distance[node] + 1
                    queue.append(neighbor)
        return distance

    first_distance = distances(corner)
    if len(graph[corner]) == 1:
        row = [0] * n
        for node, distance in enumerate(first_distance):
            row[distance] = node
        return [row]
    other = min((node for node in range(n) if node != corner and len(graph[node]) == 2),
                key=lambda node: (first_distance[node], node))
    second_distance = distances(other)
    width = first_distance[other] + 1
    height = n // width
    answer = [[0] * width for _ in range(height)]
    for node in range(n):
        row = (first_distance[node] + second_distance[node] - width + 1) // 2
        column = (first_distance[node] - second_distance[node] + width - 1) // 2
        answer[row][column] = node
    return answer


class Solution:
    def constructGridLayout(self, n: int, edges: list[list[int]]) -> list[list[int]]:
        return solve(n, edges)
