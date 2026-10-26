"""2039. The Time When the Network Becomes Idle: combine shortest round trips with the final resend strictly before the first reply."""
from collections import deque


def solve(edges: list[list[int]], patience: list[int]) -> int:
    """O(n + e) time and O(n + e) auxiliary space; inputs are read-only."""
    graph = [[] for _ in patience]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    distance = [-1] * len(patience)
    distance[0] = 0
    queue = deque([0])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if distance[neighbor] == -1:
                distance[neighbor] = distance[node] + 1
                queue.append(neighbor)
    answer = 0
    for node in range(1, len(patience)):
        trip = 2 * distance[node]
        last_send = (trip - 1) // patience[node] * patience[node]
        answer = max(answer, last_send + trip + 1)
    return answer


class Solution:
    def networkBecomesIdle(self, edges: list[list[int]], patience: list[int]) -> int:
        return solve(edges, patience)
