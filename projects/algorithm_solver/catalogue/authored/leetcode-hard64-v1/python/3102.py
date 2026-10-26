"""3102. Minimize Manhattan Distances: remove only an extremal point in rotated coordinates."""


def solve(points: list[list[int]]) -> int:
    """O(n) time and O(1) auxiliary space. Inputs are preserved."""
    minimum_sum = maximum_sum = minimum_difference = maximum_difference = 0
    for index, (x, y) in enumerate(points):
        if x + y < sum(points[minimum_sum]):
            minimum_sum = index
        if x + y > sum(points[maximum_sum]):
            maximum_sum = index
        if x - y < points[minimum_difference][0] - points[minimum_difference][1]:
            minimum_difference = index
        if x - y > points[maximum_difference][0] - points[maximum_difference][1]:
            maximum_difference = index
    answer = float('inf')
    for removed in {minimum_sum, maximum_sum, minimum_difference, maximum_difference}:
        low_sum = low_difference = float('inf')
        high_sum = high_difference = float('-inf')
        for index, (x, y) in enumerate(points):
            if index == removed:
                continue
            low_sum = min(low_sum, x + y)
            high_sum = max(high_sum, x + y)
            low_difference = min(low_difference, x - y)
            high_difference = max(high_difference, x - y)
        answer = min(answer, max(high_sum - low_sum, high_difference - low_difference))
    return int(answer)


class Solution:
    def minimumDistance(self, points: list[list[int]]) -> int:
        return solve(points)
