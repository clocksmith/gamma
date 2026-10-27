"""447. Number of Boomerangs."""

def solve(points: list[list[int]]) -> int:
    answer = 0
    for x, y in points:
        counts = {}
        for a, b in points:
            distance = (x - a) ** 2 + (y - b) ** 2
            counts[distance] = counts.get(distance, 0) + 1
        answer += sum(count * (count - 1) for count in counts.values())
    return answer


class Solution:
    def numberOfBoomerangs(self, points: list[list[int]]) -> int:
        return solve(points)
