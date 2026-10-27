def solve(edges):
    """Iterative rerooting; traversing to v costs 2 - (v % 2)."""
    n = len(edges) + 1
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    parent = [-1] * n
    order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    first = [0] * n
    second = [0] * n
    owner = [-1] * n
    for u in reversed(order):
        for v in graph[u]:
            if parent[v] != u:
                continue
            distance = first[v] + 2 - v % 2
            if distance > first[u]:
                second[u], first[u], owner[u] = first[u], distance, v
            elif distance > second[u]:
                second[u] = distance
    upward = [0] * n
    answer = [0] * n
    for u in order:
        answer[u] = max(first[u], upward[u])
        for v in graph[u]:
            if parent[v] == u:
                sibling = second[u] if owner[u] == v else first[u]
                upward[v] = max(upward[u], sibling) + 2 - u % 2
    return answer
