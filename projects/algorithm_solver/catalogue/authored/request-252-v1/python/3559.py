def solve(edges, queries):
    n = len(edges) + 1
    adjacency = [[] for _ in range(n + 1)]
    for u, v in edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    depth = [0] * (n + 1)
    parent = [0] * (n + 1)
    order = [1]
    for u in order:
        for v in adjacency[u]:
            if v != parent[u]:
                parent[v] = u
                depth[v] = depth[u] + 1
                order.append(v)
    ancestors = [parent]
    for level in range(1, n.bit_length()):
        previous = ancestors[-1]
        ancestors.append([previous[previous[u]] for u in range(n + 1)])
    powers = [1] * n
    for i in range(1, n):
        powers[i] = powers[i - 1] * 2 % 1_000_000_007

    def lca(u, v):
        if depth[u] < depth[v]:
            u, v = v, u
        difference = depth[u] - depth[v]
        for level in range(len(ancestors)):
            if difference >> level & 1:
                u = ancestors[level][u]
        if u == v:
            return u
        for level in range(len(ancestors) - 1, -1, -1):
            if ancestors[level][u] != ancestors[level][v]:
                u, v = ancestors[level][u], ancestors[level][v]
        return parent[u]

    answer = []
    for u, v in queries:
        distance = depth[u] + depth[v] - 2 * depth[lca(u, v)]
        answer.append(powers[distance - 1] if distance else 0)
    return answer
