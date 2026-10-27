"""444. Sequence Reconstruction. Require a unique topological choice matching nums at every step."""

from collections import deque

def solve(nums: list[int], sequences: list[list[int]]) -> bool:
    n = len(nums)
    graph = [set() for _ in range(n + 1)]
    indegree = [0] * (n + 1)
    seen = set()
    for sequence in sequences:
        for value in sequence:
            if not 1 <= value <= n:
                return False
            seen.add(value)
        for a, b in zip(sequence, sequence[1:]):
            if b not in graph[a]:
                graph[a].add(b)
                indegree[b] += 1
    if len(seen) != n:
        return False
    queue = deque(value for value in range(1, n + 1) if indegree[value] == 0)
    index = 0
    while queue:
        if len(queue) != 1:
            return False
        value = queue.popleft()
        if index >= n or nums[index] != value:
            return False
        index += 1
        for neighbor in graph[value]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return index == n


class Solution:
    def sequenceReconstruction(self, nums: list[int], sequences: list[list[int]]) -> bool:
        return solve(nums, sequences)
