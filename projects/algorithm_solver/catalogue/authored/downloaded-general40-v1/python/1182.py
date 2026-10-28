"""1182. Shortest Distance to Target Color (Medium).

Specification: https://leetcode.com/problems/shortest-distance-to-target-color/description/
"""


def _nearest(positions, target):
    left, right = 0, len(positions) - 1
    best = float('inf')
    while left <= right:
        mid = (left + right) // 2
        best = min(best, abs(positions[mid] - target))
        if positions[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return best


def solve(colors: list[int], queries: list[list[int]]) -> list[int]:
    positions = [[], [], [], []]
    for i, color in enumerate(colors):
        positions[color].append(i)
    result = []
    for index, color in queries:
        best = _nearest(positions[color], index)
        result.append(-1 if best == float('inf') else best)
    return result


class Solution:
    def shortestDistanceColor(self, colors: list[int], queries: list[list[int]]) -> list[int]:
        return solve(colors, queries)
