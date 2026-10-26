"""2139. Minimum Moves to Reach Target Score: work backward by halving whenever allowed and removing an odd excess first."""


def solve(target: int, maxDoubles: int) -> int:
    """O(log target) time and O(1) auxiliary space; inputs are read-only."""
    current = target
    doubles = maxDoubles
    moves = 0
    while current > 1 and doubles > 0:
        if current % 2:
            current -= 1
            moves += 1
        current //= 2
        doubles -= 1
        moves += 1
    return moves + current - 1


class Solution:
    def minMoves(self, target: int, maxDoubles: int) -> int:
        return solve(target, maxDoubles)
