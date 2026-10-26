"""1870. Minimum Speed to Arrive on Time: binary search speed using exact hundredths for the final arrival comparison."""


def solve(dist: list[int], hour: float) -> int:
    """O(n * log(10^7)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    hundredths = round(hour * 100)

    def feasible(speed: int) -> bool:
        whole_hours = 0
        for index in range(len(dist) - 1):
            whole_hours += (dist[index] + speed - 1) // speed
            if whole_hours * 100 >= hundredths:
                return False
        remaining = hundredths - whole_hours * 100
        return dist[-1] * 100 <= remaining * speed

    low, high = 1, 10_000_000
    if not feasible(high):
        return -1
    while low < high:
        middle = (low + high) // 2
        if feasible(middle):
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minSpeedOnTime(self, dist: list[int], hour: float) -> int:
        return solve(dist, hour)
