"""1560. Most Visited Sector in a Circular Track (Easy).

Specification: https://leetcode.com/problems/most-visited-sector-in-a-circular-track/description/
"""


def solve(n: int, rounds: list[int]) -> list[int]:
    """O(n) time, O(n) output space; complete laps affect all sectors equally."""
    start, finish = rounds[0], rounds[-1]
    result = []
    for sector in range(1, n + 1):
        if start <= finish:
            most_visited = start <= sector <= finish
        else:
            most_visited = sector >= start or sector <= finish
        if most_visited:
            result.append(sector)
    return result


class Solution:
    def mostVisited(self, n: int, rounds: list[int]) -> list[int]:
        return solve(n, rounds)
