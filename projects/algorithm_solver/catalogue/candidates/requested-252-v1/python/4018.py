"""4018. Total Sum of Interaction Cost in Tree Groups II.

Specification: https://leetcode.com/problems/total-sum-of-interaction-cost-in-tree-groups-ii/description/
"""

from __future__ import annotations


def solve(n: int, edges: list[list[int]], group: list[int]) -> int:
    """O(n log n) expected time and O(n) live auxiliary space; small-to-large map merging. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * n
    parent[0] = 0
    depth = [0] * n
    order = [0]
    for node in order:
        for next_node in graph[node]:
            if next_node != parent[node]:
                parent[next_node] = node
                depth[next_node] = depth[node] + 1
                order.append(next_node)
    bags = [None] * n
    answer = 0
    for node in reversed(order):
        bag = {group[node]: [1, depth[node]]}
        for child in graph[node]:
            if parent[child] != node or child == node:
                continue
            other = bags[child]
            if len(bag) < len(other):
                bag, other = other, bag
            for label, (count, depth_sum) in other.items():
                previous = bag.get(label)
                if previous is not None:
                    answer += (previous[0] * depth_sum + count * previous[1]
                               - 2 * depth[node] * previous[0] * count)
                    previous[0] += count
                    previous[1] += depth_sum
                else:
                    bag[label] = [count, depth_sum]
            bags[child] = None
        bags[node] = bag
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
