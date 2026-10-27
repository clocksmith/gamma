def solve(n, edges, k):
    parent = list(range(n))
    size = [1] * n

    def find(vertex):
        while vertex != parent[vertex]:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    ordered = sorted(edges, key=lambda edge: edge[2], reverse=True)
    components = n
    index = 0
    while index < len(ordered):
        time = ordered[index][2]
        while index < len(ordered) and ordered[index][2] == time:
            a, b, _ = ordered[index]
            a, b = find(a), find(b)
            if a != b:
                if size[a] < size[b]:
                    a, b = b, a
                parent[b] = a
                size[a] += size[b]
                components -= 1
            index += 1
        # At t=time these edges are absent; immediately below time they are present.
        if components < k:
            return time
    return 0
