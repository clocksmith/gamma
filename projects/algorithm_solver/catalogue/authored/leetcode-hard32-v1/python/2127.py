"""2127. Maximum Employees to Be Invited to a Meeting."""

from collections import deque


def solve(favorite: list[int]) -> int:
    """O(n) time and space; prune chains, then combine two-cycles or select one longer cycle."""
    size = len(favorite)
    indegree = [0] * size
    for node in favorite:
        indegree[node] += 1
    depth = [1] * size
    queue = deque(index for index in range(size) if indegree[index] == 0)
    while queue:
        node = queue.popleft()
        neighbor = favorite[node]
        depth[neighbor] = max(depth[neighbor], depth[node] + 1)
        indegree[neighbor] -= 1
        if indegree[neighbor] == 0:
            queue.append(neighbor)
    longest = 0
    pairs = 0
    for start in range(size):
        if indegree[start] == 0:
            continue
        length = 0
        node = start
        while indegree[node] != 0:
            indegree[node] = 0
            length += 1
            node = favorite[node]
        if length == 2:
            pairs += depth[start] + depth[favorite[start]]
        else:
            longest = max(longest, length)
    return max(longest, pairs)


class Solution:
    def maximumInvitations(self, favorite: list[int]) -> int:
        return solve(favorite)
