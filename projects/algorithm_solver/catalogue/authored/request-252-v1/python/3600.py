def solve(n, edges, k):
    def feasible(threshold):
        parent = list(range(n))
        sizes = [1] * n
        components = n

        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u

        def union(u, v):
            nonlocal components
            u, v = find(u), find(v)
            if u == v:
                return False
            if sizes[u] < sizes[v]:
                u, v = v, u
            parent[v] = u
            sizes[u] += sizes[v]
            components -= 1
            return True

        for u, v, strength, must in edges:
            if must and (strength < threshold or not union(u, v)):
                return False
        for u, v, strength, must in edges:
            if not must and strength >= threshold:
                union(u, v)
        used = 0
        for u, v, strength, must in edges:
            if not must and strength < threshold <= strength * 2 and union(u, v):
                used += 1
        return components == 1 and used <= k

    if not feasible(0):
        return -1
    low, high = 0, 2 * max(edge[2] for edge in edges)
    while low < high:
        mid = (low + high + 1) // 2
        if feasible(mid):
            low = mid
        else:
            high = mid - 1
    return low
