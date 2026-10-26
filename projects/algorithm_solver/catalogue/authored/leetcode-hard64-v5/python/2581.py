"""2581. Count Number of Possible Root Nodes. Reroot the number of correct directed parent guesses."""


def solve(edges: list[list[int]], guesses: list[list[int]], k: int) -> int:
    """O(n+g) expected time and O(n+g) space. Inputs are preserved."""
    size = len(edges) + 1
    graph = [[] for _ in range(size)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    guessed = {(first, second) for first, second in guesses}
    parent = [-1] * size
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    score = [0] * size
    score[0] = sum((parent[node], node) in guessed for node in order[1:])
    for node in order[1:]:
        previous = parent[node]
        score[node] = score[previous] - ((previous, node) in guessed) + ((node, previous) in guessed)
    return sum(value >= k for value in score)


class Solution:
    def rootCount(self, edges: list[list[int]], guesses: list[list[int]], k: int) -> int:
        return solve(edges, guesses, k)
