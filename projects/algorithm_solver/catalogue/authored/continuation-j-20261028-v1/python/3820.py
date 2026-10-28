"""Original frontend 3820 variant; qualification unknown."""

def solve(n, edges, x, y, z):
    adjacency = [[] for _ in range(n)]
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    def distances(start):
        result = [-1] * n
        result[start] = 0
        queue = [start]
        for node in queue:
            for other in adjacency[node]:
                if result[other] == -1:
                    result[other] = result[node] + 1
                    queue.append(other)
        return result
    dx, dy, dz = distances(x), distances(y), distances(z)
    answer = 0
    for values in zip(dx, dy, dz):
        a, b, c = sorted(values)
        answer += a * a + b * b == c * c
    return answer


class Solution:
    def specialNodes(self, n, edges, x, y, z):
        return solve(n, edges, x, y, z)
