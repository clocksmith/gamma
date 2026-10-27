"""593. Valid Square."""

def solve(p1: list[int], p2: list[int], p3: list[int], p4: list[int]) -> bool:
    points = [p1, p2, p3, p4]
    distances = sorted((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2
                       for i in range(4) for j in range(i + 1, 4))
    return (distances[0] > 0 and distances[0] == distances[1] == distances[2] == distances[3]
            and distances[4] == distances[5] == 2 * distances[0])


class Solution:
    def validSquare(self, p1: list[int], p2: list[int], p3: list[int], p4: list[int]) -> bool:
        return solve(p1, p2, p3, p4)
