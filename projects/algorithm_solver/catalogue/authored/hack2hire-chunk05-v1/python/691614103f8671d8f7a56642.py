"""Original hack2hire:691614103f8671d8f7a56642; inferred public-preview contract; qualification unknown."""
from collections import deque

def clusterSummary(parents):
    n = len(parents)
    if not n:
        return {'count': 0, 'topology': ''}
    children = [[] for _ in parents]
    root = parents.index(-1)
    for node, parent in enumerate(parents):
        if parent >= 0:
            children[parent].append(node)
    pending = [len(row) for row in children]
    queue = deque(i for i in range(n) if not pending[i])
    counts = [1] * n
    topology = [''] * n
    while queue:
        node = queue.popleft()
        topology[node] = str(node) + ('(' + ','.join(topology[c] for c in children[node]) + ')' if children[node] else '')
        parent = parents[node]
        if parent >= 0:
            counts[parent] += counts[node]
            pending[parent] -= 1
            if pending[parent] == 0:
                queue.append(parent)
    return {'count': counts[root], 'topology': topology[root]}

solve = clusterSummary

class Solution:
    clusterSummary = staticmethod(clusterSummary)
