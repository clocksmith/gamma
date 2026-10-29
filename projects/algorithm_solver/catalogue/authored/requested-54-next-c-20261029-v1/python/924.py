def solve(graph, initial):
    n = len(graph)
    label = [-1]*n
    sizes = []
    for start in range(n):
        if label[start] >= 0:
            continue
        component = len(sizes)
        label[start] = component
        stack = [start]
        count = 0
        while stack:
            u = stack.pop()
            count += 1
            for v in range(n):
                if graph[u][v] and label[v] < 0:
                    label[v] = component
                    stack.append(v)
        sizes.append(count)
    seeds = [0]*len(sizes)
    for x in initial:
        seeds[label[x]] += 1
    return min(initial,key=lambda x: (-(sizes[label[x]] if seeds[label[x]] == 1 else 0),x))

class Solution:
    def minMalwareSpread(self, graph, initial):
        return solve(graph, initial)
