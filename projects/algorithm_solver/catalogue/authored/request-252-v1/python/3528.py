# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(conversions):
    graph = [[] for _ in range(len(conversions) + 1)]
    for source, target, factor in conversions:
        graph[source].append((target, factor))
    answer = [0] * len(graph)
    answer[0] = 1
    stack = [0]
    while stack:
        source = stack.pop()
        for target, factor in graph[source]:
            answer[target] = answer[source] * factor % 1_000_000_007
            stack.append(target)
    return answer
