"""2077. Paths in Maze That Lead to Same Room: count triangles once using degree-ordered forward edges."""


def solve(n: int, corridors: list[list[int]]) -> int:
    """O(n + e * sqrt(e)) expected time and O(n + e) auxiliary space; inputs are read-only."""
    degree = [0] * n
    for left, right in corridors:
        degree[left - 1] += 1
        degree[right - 1] += 1
    forward = [set() for _ in range(n)]
    for left, right in corridors:
        left -= 1
        right -= 1
        if (degree[left], left) > (degree[right], right):
            left, right = right, left
        forward[left].add(right)
    answer = 0
    for first in range(n):
        for second in forward[first]:
            for third in forward[second]:
                if third in forward[first]:
                    answer += 1
    return answer


class Solution:
    def numberOfPaths(self, n: int, corridors: list[list[int]]) -> int:
        return solve(n, corridors)
