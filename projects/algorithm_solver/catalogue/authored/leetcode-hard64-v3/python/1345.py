"""1345. Jump Game IV: BFS with each equal-value bucket consumed once; O(n) expected time and O(n) space."""

from collections import deque


def solve(arr: list[int]) -> int:
    positions = {}
    for index, value in enumerate(arr):
        positions.setdefault(value, []).append(index)
    seen = [False] * len(arr)
    seen[0] = True
    queue = deque([(0, 0)])
    while queue:
        index, distance = queue.popleft()
        if index == len(arr) - 1:
            return distance
        neighbors = positions.pop(arr[index], [])
        neighbors.extend((index - 1, index + 1))
        for neighbor in neighbors:
            if 0 <= neighbor < len(arr) and not seen[neighbor]:
                seen[neighbor] = True
                queue.append((neighbor, distance + 1))
    return -1


class Solution:
    def minJumps(self, arr: list[int]) -> int:
        return solve(arr)
