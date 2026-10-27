# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(edges):
    graph = [[] for _ in range(len(edges) + 2)]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    stack = [(1, 0, 0)]
    deepest = 0
    while stack:
        node, parent, depth = stack.pop()
        deepest = max(deepest, depth)
        for child in graph[node]:
            if child != parent:
                stack.append((child, node, depth + 1))
    return pow(2, deepest - 1, 1_000_000_007)
