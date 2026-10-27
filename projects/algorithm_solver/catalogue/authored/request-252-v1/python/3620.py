from collections import deque


def solve(edges, online, k):
    n = len(online)
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for u, v, cost in edges:
        graph[u].append((v, cost))
        indegree[v] += 1
    queue = deque(i for i in range(n) if indegree[i] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v, _ in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    def feasible(threshold):
        distance = [float('inf')] * n
        distance[0] = 0
        for u in order:
            if not online[u] or distance[u] > k:
                continue
            for v, cost in graph[u]:
                if online[v] and cost >= threshold:
                    distance[v] = min(distance[v], distance[u] + cost)
        return distance[-1] <= k

    if not feasible(0):
        return -1
    low, high = 0, max((cost for _, _, cost in edges), default=0)
    while low < high:
        mid = (low + high + 1) // 2
        if feasible(mid):
            low = mid
        else:
            high = mid - 1
    return low
