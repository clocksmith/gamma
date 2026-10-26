"""3486. Longest Special Path II.

The second-largest predecessor depth of repeated values bounds a path containing at most one repeated pair; iterative O(n) time and space. Inputs are preserved.
"""

def solve(edges: list[list[int]], nums: list[int]) -> list[int]:
    graph = [[] for _ in nums]
    for first, second, weight in edges:
        graph[first].append((second, weight))
        graph[second].append((first, weight))
    last, distances = {}, []
    answer, count = 0, 1
    stack = [(0, -1, 0, -1, -1, False, -1)]
    while stack:
        node, parent, distance, largest, second, exiting, previous = stack.pop()
        value = nums[node]
        if exiting:
            distances.pop()
            if previous == -1:
                del last[value]
            else:
                last[value] = previous
            continue
        depth = len(distances)
        previous = last.get(value, -1)
        if previous > largest:
            largest, second = previous, largest
        elif previous > second:
            second = previous
        start = second + 1
        distances.append(distance)
        last[value] = depth
        length, nodes = distance - distances[start], depth - start + 1
        if length > answer or (length == answer and nodes < count):
            answer, count = length, nodes
        stack.append((node, parent, distance, largest, second, True, previous))
        for child, weight in graph[node]:
            if child != parent:
                stack.append((child, node, distance + weight, largest, second, False, -1))
    return [answer, count]


class Solution:
    def longestSpecialPath(self, edges: list[list[int]], nums: list[int]) -> list[int]:
        return solve(edges, nums)
