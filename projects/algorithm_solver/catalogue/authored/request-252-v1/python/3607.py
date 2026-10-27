# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(c, connections, queries):
    parent = list(range(c + 1))
    size = [1] * (c + 1)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in connections:
        a, b = find(a), find(b)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
    groups = [[] for _ in range(c + 1)]
    roots = [find(node) for node in range(c + 1)]
    for node in range(1, c + 1):
        groups[roots[node]].append(node)
    online = [True] * (c + 1)
    positions = [0] * (c + 1)
    answer = []
    for kind, node in queries:
        if kind == 2:
            online[node] = False
        elif online[node]:
            answer.append(node)
        else:
            root = roots[node]
            group = groups[root]
            while positions[root] < len(group) and not online[group[positions[root]]]:
                positions[root] += 1
            answer.append(group[positions[root]] if positions[root] < len(group) else -1)
    return answer
