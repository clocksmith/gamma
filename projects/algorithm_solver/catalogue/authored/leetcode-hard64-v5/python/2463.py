"""2463. Minimum Total Distance Traveled. Assign consecutive sorted robots to each sorted factory."""


def solve(robot: list[int], factory: list[list[int]]) -> int:
    """O(F log F+R log R+F*R^2) time and O(F+R) space. Inputs are preserved."""
    robots = sorted(robot)
    factories = sorted(factory)
    size = len(robots)
    best = [0] + [float("inf")] * size
    for position, capacity in factories:
        current = best.copy()
        for repaired in range(1, size + 1):
            distance = 0
            for taken in range(1, min(capacity, repaired) + 1):
                distance += abs(robots[repaired - taken] - position)
                current[repaired] = min(current[repaired], best[repaired - taken] + distance)
        best = current
    return best[size]


class Solution:
    def minimumTotalDistance(self, robot: list[int], factory: list[list[int]]) -> int:
        return solve(robot, factory)
