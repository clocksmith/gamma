"""3025. Find the Number of Ways to Place People I: sweep rightward from each upper-left point while excluding blocked lower-right choices."""


def solve(points: list[list[int]]) -> int:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(points, key=lambda point: (point[0], -point[1]))
    result = 0
    for left in range(len(ordered)):
        ceiling = ordered[left][1]
        highest = float('-inf')
        for right in range(left + 1, len(ordered)):
            height = ordered[right][1]
            if highest < height <= ceiling:
                result += 1
                highest = height
    return result


class Solution:
    def numberOfPairs(self, points: list[list[int]]) -> int:
        return solve(points)
