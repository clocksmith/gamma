"""913. Cat and Mouse."""

from collections import deque


def solve(graph: list[list[int]]) -> int:
    """Retrograde game analysis: O(n * (n + E)) time, O(n^2) space; 0 means draw."""
    size = len(graph)
    outcome = [[[0, 0] for _ in range(size)] for _ in range(size)]
    degree = [[[0, 0] for _ in range(size)] for _ in range(size)]
    queue = deque()
    for mouse in range(size):
        for cat in range(1, size):
            degree[mouse][cat][0] = len(graph[mouse])
            degree[mouse][cat][1] = sum(node != 0 for node in graph[cat])
            for turn in range(2):
                winner = 1 if mouse == 0 else 2 if mouse == cat else 0
                if winner == 0 and degree[mouse][cat][turn] == 0:
                    winner = 2 if turn == 0 else 1
                if winner:
                    outcome[mouse][cat][turn] = winner
                    queue.append((mouse, cat, turn))
    while queue:
        mouse, cat, turn = queue.popleft()
        winner = outcome[mouse][cat][turn]
        parent_turn = 1 - turn
        previous_nodes = graph[cat] if turn == 0 else graph[mouse]
        for previous in previous_nodes:
            parent_mouse = mouse if turn == 0 else previous
            parent_cat = previous if turn == 0 else cat
            if parent_cat == 0 or outcome[parent_mouse][parent_cat][parent_turn]:
                continue
            if winner == parent_turn + 1:
                outcome[parent_mouse][parent_cat][parent_turn] = winner
            else:
                degree[parent_mouse][parent_cat][parent_turn] -= 1
                if degree[parent_mouse][parent_cat][parent_turn] != 0:
                    continue
                outcome[parent_mouse][parent_cat][parent_turn] = 2 - parent_turn
            queue.append((parent_mouse, parent_cat, parent_turn))
    return outcome[1][2][0]


class Solution:
    def catMouseGame(self, graph: list[list[int]]) -> int:
        return solve(graph)
