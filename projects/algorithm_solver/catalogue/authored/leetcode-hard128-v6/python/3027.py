"""3027. Find the Number of Ways to Place People II.

Sort by increasing x and decreasing y; sweep the highest blocking y for each upper-left corner. O(n^2) time, O(n) space. Inputs are preserved.
"""

def solve(points: list[list[int]]) -> int:
    ordered = sorted(points, key=lambda point: (point[0], -point[1]))
    answer = 0
    for index, (_, upper) in enumerate(ordered):
        blocked = float('-inf')
        for other in range(index + 1, len(ordered)):
            lower = ordered[other][1]
            if blocked < lower <= upper:
                answer += 1
                blocked = lower
    return answer


class Solution:
    def numberOfPairs(self, points: list[list[int]]) -> int:
        return solve(points)
