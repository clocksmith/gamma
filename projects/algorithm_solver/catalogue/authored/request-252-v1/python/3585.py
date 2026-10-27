# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(n, edges, queries):
    graph = [[] for _ in range(n)]
    for a, b, weight in edges:
        graph[a].append((b, weight))
        graph[b].append((a, weight))
    depth, distance, parent = [0] * n, [0] * n, [0] * n
    stack = [0]
    while stack:
        node = stack.pop()
        for child, weight in graph[node]:
            if child != parent[node]:
                parent[child] = node
                depth[child] = depth[node] + 1
                distance[child] = distance[node] + weight
                stack.append(child)
    up = [parent]
    for _ in range(1, n.bit_length()):
        previous = up[-1]
        up.append([previous[previous[v]] for v in range(n)])

    def lca(a, b):
        if depth[a] < depth[b]:
            a, b = b, a
        difference = depth[a] - depth[b]
        for level in range(len(up)):
            if difference >> level & 1:
                a = up[level][a]
        if a == b:
            return a
        for level in range(len(up) - 1, -1, -1):
            if up[level][a] != up[level][b]:
                a, b = up[level][a], up[level][b]
        return parent[a]

    answers = []
    for a, b in queries:
        ancestor = lca(a, b)
        total = distance[a] + distance[b] - 2 * distance[ancestor]
        if total == 0:
            answers.append(a)
        elif 2 * (distance[a] - distance[ancestor]) >= total:
            node = a
            for level in range(len(up) - 1, -1, -1):
                candidate = up[level][node]
                if depth[candidate] >= depth[ancestor] and 2 * (distance[a] - distance[candidate]) < total:
                    node = candidate
            answers.append(parent[node])
        else:
            node = b
            for level in range(len(up) - 1, -1, -1):
                candidate = up[level][node]
                if depth[candidate] >= depth[ancestor] and 2 * (distance[b] - distance[candidate]) <= total:
                    node = candidate
            answers.append(node)
    return answers
