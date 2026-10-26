"""1937. Maximum Number of Points with Cost: propagate the best previous-row score from both directions."""


def solve(points: list[list[int]]) -> int:
    """O(rows * columns) time and O(columns) auxiliary space; inputs are read-only."""
    columns = len(points[0])
    previous = points[0][:]
    for row in range(1, len(points)):
        next_scores = [0] * columns
        best = previous[0]
        for column in range(columns):
            best = max(best - 1, previous[column])
            next_scores[column] = points[row][column] + best
        best = previous[-1]
        for column in range(columns - 1, -1, -1):
            best = max(best - 1, previous[column])
            next_scores[column] = max(next_scores[column], points[row][column] + best)
        previous = next_scores
    return max(previous)


class Solution:
    def maxPoints(self, points: list[list[int]]) -> int:
        return solve(points)
