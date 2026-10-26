"""1766. Tree of Coprimes.

Iterative DFS with the nearest active ancestor for each value in [1,50]; O(50*n) time, O(n + 50^2) space. Inputs are preserved.
"""

from math import gcd


def solve(nums: list[int], edges: list[list[int]]) -> list[int]:
    graph = [[] for _ in nums]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    coprime = [[other for other in range(1, 51) if gcd(value, other) == 1] for value in range(51)]
    nearest = [(-1, -1)] * 51
    answer = [-1] * len(nums)
    stack = [(0, -1, 0, None)]
    while stack:
        node, parent, depth, restore = stack.pop()
        value = nums[node]
        if restore is not None:
            nearest[value] = restore
            continue
        best = (-1, -1)
        for other in coprime[value]:
            if nearest[other][1] > best[1]:
                best = nearest[other]
        answer[node] = best[0]
        old = nearest[value]
        nearest[value] = (node, depth)
        stack.append((node, parent, depth, old))
        for neighbor in reversed(graph[node]):
            if neighbor != parent:
                stack.append((neighbor, node, depth + 1, None))
    return answer


class Solution:
    def getCoprimes(self, nums: list[int], edges: list[list[int]]) -> list[int]:
        return solve(nums, edges)
