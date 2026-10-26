"""3067. Count Pairs of Connectable Servers in a Weighted Tree Network: combine divisible-distance nodes from distinct branches of each tree root."""


def solve(edges: list[list[int]], signalSpeed: int) -> list[int]:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    size = len(edges) + 1
    graph = [[] for _ in range(size)]
    for left, right, weight in edges:
        graph[left].append((right, weight))
        graph[right].append((left, weight))
    result = [0] * size
    for root in range(size):
        previous = 0
        for child, weight in graph[root]:
            count = 0
            stack = [(child, root, weight % signalSpeed)]
            while stack:
                node, parent, distance = stack.pop()
                if distance == 0:
                    count += 1
                for neighbor, edge_weight in graph[node]:
                    if neighbor != parent:
                        stack.append((neighbor, node, (distance + edge_weight) % signalSpeed))
            result[root] += previous * count
            previous += count
    return result


class Solution:
    def countPairsOfConnectableServers(self, edges: list[list[int]], signalSpeed: int) -> list[int]:
        return solve(edges, signalSpeed)
