"""3544. Subtree Inversion Sum.

Bottom-up tree states track inherited sign and the remaining inversion cooldown; O(n*k) time and O(n*k) worst-case space. Inputs are preserved.
"""

from array import array


def solve(edges: list[list[int]], nums: list[int], k: int) -> int:
    n = len(nums)
    graph = [[] for _ in nums]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = [-1] * n
    order = [0]
    for node in order:
        for child in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    states = [None] * n
    for node in reversed(order):
        current = array('q', [nums[node]]) * k + array('q', [-nums[node]]) * k
        flip_positive, flip_negative = -nums[node], nums[node]
        for child in graph[node]:
            if child == parent[node]:
                continue
            other = states[child]
            flip_positive += other[2 * k - 1]
            flip_negative += other[k - 1]
            for wait in range(k):
                following = max(0, wait - 1)
                current[wait] += other[following]
                current[k + wait] += other[k + following]
            states[child] = None
        current[0] = max(current[0], flip_positive)
        current[k] = max(current[k], flip_negative)
        states[node] = current
    return states[0][0]


class Solution:
    def subtreeInversionSum(self, edges: list[list[int]], nums: list[int], k: int) -> int:
        return solve(edges, nums, k)
