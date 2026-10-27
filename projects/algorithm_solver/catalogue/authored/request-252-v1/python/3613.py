def solve(n, edges, k):
    parent = list(range(n))
    size = [1] * n
    components = n

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    if components <= k:
        return 0
    for u, v, weight in sorted(edges, key=lambda edge: edge[2]):
        u, v = find(u), find(v)
        if u == v:
            continue
        if size[u] < size[v]:
            u, v = v, u
        parent[v] = u
        size[u] += size[v]
        components -= 1
        if components <= k:
            return weight
    raise ValueError('The input graph must be connected')
