"""3203. Find Minimum Diameter After Merging Two Trees.

Connect tree centers after computing both diameters with BFS; O(n+m) time and space. Inputs are preserved.
"""

def solve(edges1: list[list[int]], edges2: list[list[int]]) -> int:
    def diameter(edges):
        graph = [[] for _ in range(len(edges) + 1)]
        for a, b in edges:
            graph[a].append(b)
            graph[b].append(a)

        def farthest(start):
            distance = [-1] * len(graph)
            distance[start] = 0
            queue = [start]
            for node in queue:
                for neighbor in graph[node]:
                    if distance[neighbor] == -1:
                        distance[neighbor] = distance[node] + 1
                        queue.append(neighbor)
            return queue[-1], distance[queue[-1]]

        return farthest(farthest(0)[0])[1]

    first, second = diameter(edges1), diameter(edges2)
    return max(first, second, (first + 1) // 2 + (second + 1) // 2 + 1)


class Solution:
    def minimumDiameterAfterMerge(self, edges1: list[list[int]], edges2: list[list[int]]) -> int:
        return solve(edges1, edges2)
