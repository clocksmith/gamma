# 399 — Evaluate Division. Original implementation; authored candidate, not independently qualified.
def solve(equations, values, queries):
    graph = {}
    for (a, b), value in zip(equations, values):
        graph.setdefault(a, []).append((b, value))
        graph.setdefault(b, []).append((a, 1 / value))
    result = []
    for start, target in queries:
        answer = -1.0
        if start in graph and target in graph:
            stack, seen = [(start, 1.0)], {start}
            while stack:
                current, ratio = stack.pop()
                if current == target:
                    answer = ratio
                    break
                for neighbor, weight in graph[current]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append((neighbor, ratio * weight))
        result.append(answer)
    return result

calcEquation = solve

class Solution:
    calcEquation = staticmethod(solve)
