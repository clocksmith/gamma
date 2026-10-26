"""2751. Robot Collisions. Resolve sorted encounters against a stack of right-moving robots."""


def solve(positions: list[int], healths: list[int], directions: str) -> list[int]:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    remaining = healths.copy()
    rightward = []
    for robot in sorted(range(len(positions)), key=positions.__getitem__):
        if directions[robot] == "R":
            rightward.append(robot)
            continue
        while rightward and remaining[robot] > 0:
            other = rightward[-1]
            if remaining[other] < remaining[robot]:
                remaining[other] = 0
                remaining[robot] -= 1
                rightward.pop()
            elif remaining[other] > remaining[robot]:
                remaining[other] -= 1
                remaining[robot] = 0
            else:
                remaining[other] = remaining[robot] = 0
                rightward.pop()
    return [health for health in remaining if health > 0]


class Solution:
    def survivedRobotsHealths(self, positions: list[int], healths: list[int], directions: str) -> list[int]:
        return solve(positions, healths, directions)
