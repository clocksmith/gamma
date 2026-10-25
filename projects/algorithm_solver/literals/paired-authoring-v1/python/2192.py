class Solution:
    def getAncestors(self, n: int, edges: list[list[int]]) -> list[list[int]]:
        neighbors = [[] for _ in range(n)]
        indegree = [0] * n
        for first, second in edges:
            neighbors[first].append(second)
            indegree[second] += 1
        ancestors = [set() for _ in range(n)]
        queue = [node for node in range(n) if indegree[node] == 0]
        head = 0
        while head < len(queue):
            node = queue[head]
            head += 1
            for neighbor in neighbors[node]:
                ancestors[neighbor].add(node)
                for ancestor in ancestors[node]:
                    ancestors[neighbor].add(ancestor)
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        return [sorted(group) for group in ancestors]
