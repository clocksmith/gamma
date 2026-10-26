"""2188. Minimum Time to Finish the Race."""


def solve(tires: list[list[int]], changeTime: int, numLaps: int) -> int:
    """Bounded same-tire stints followed by partition DP; O((T+N)*L) time and O(N) space. Inputs are preserved."""
    stint = [float('inf')] * (numLaps + 1)
    longest = 0
    for first, ratio in tires:
        lap = first
        total = 0
        for length in range(1, numLaps + 1):
            total += lap
            stint[length] = min(stint[length], total)
            longest = max(longest, length)
            if lap * ratio >= changeTime + first:
                break
            lap *= ratio
    best = [float('inf')] * (numLaps + 1)
    best[0] = -changeTime
    for laps in range(1, numLaps + 1):
        for length in range(1, min(laps, longest) + 1):
            best[laps] = min(best[laps], best[laps - length] + changeTime + stint[length])
    return best[numLaps]


class Solution:
    def minimumFinishTime(self, tires: list[list[int]], changeTime: int, numLaps: int) -> int:
        return solve(tires, changeTime, numLaps)
