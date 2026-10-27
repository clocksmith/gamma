"""3967. Finish Time of Tasks II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/finish-time-of-tasks-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3967.Finish%20Time%20of%20Tasks%20II/README_EN.md
Complexity: O(n) arbitrary-integer operations and O(n) stored integers; bit complexity depends on potentially exponential finish times.
Unlike part I, the consulted statement gives no 2^53 bound. JavaScript solve returns BigInt, Python int; JSON must use decimal-string transport. Iterative rerooting uses two extrema with multiplicity, including tied children. Inputs preserved; native method pending.
"""

from __future__ import annotations

def solve(n, edges, baseTime):
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * n
    order = [0]
    for node in order:
        for child in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    down = baseTime.copy()
    for node in reversed(order):
        values = [down[child] for child in graph[node] if child != parent[node]]
        if values:
            low, high = min(values), max(values)
            down[node] = high + (high - low) + baseTime[node]
    up = [0] * n
    answer = down[0]
    for node in order:
        incoming = [up[node] if neighbor == parent[node] else down[neighbor] for neighbor in graph[node]]
        if not incoming:
            answer = min(answer, baseTime[node])
            continue
        low1 = low2 = high1 = high2 = None
        low_index = high_index = -1
        for index, value in enumerate(incoming):
            if low1 is None or value < low1:
                low2, low1, low_index = low1, value, index
            elif low2 is None or value < low2:
                low2 = value
            if high1 is None or value > high1:
                high2, high1, high_index = high1, value, index
            elif high2 is None or value > high2:
                high2 = value
        answer = min(answer, high1 + (high1 - low1) + baseTime[node])
        for index, child in enumerate(graph[node]):
            if child == parent[node]:
                continue
            if len(incoming) == 1:
                up[child] = baseTime[node]
            else:
                low = low2 if index == low_index else low1
                high = high2 if index == high_index else high1
                up[child] = high + (high - low) + baseTime[node]
    return answer
