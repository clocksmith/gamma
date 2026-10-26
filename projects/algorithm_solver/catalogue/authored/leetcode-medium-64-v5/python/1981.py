"""1981. Minimize the Difference Between Target and Chosen Elements: keep all attainable sums below target and only the smallest overflowing sum."""


def solve(mat: list[list[int]], target: int) -> int:
    """O(rows * columns * (target + 1)) expected time and O(target + columns) auxiliary space; inputs are read-only."""
    reachable = {0}
    for row in mat:
        choices = set(row)
        next_sums = set()
        smallest_overflow = None
        for total in reachable:
            for value in choices:
                candidate = total + value
                if candidate <= target:
                    next_sums.add(candidate)
                elif smallest_overflow is None or candidate < smallest_overflow:
                    smallest_overflow = candidate
        # All future additions are positive, so larger overflows are dominated.
        if smallest_overflow is not None:
            next_sums.add(smallest_overflow)
        reachable = next_sums
    return min(abs(total - target) for total in reachable)


class Solution:
    def minimizeTheDifference(self, mat: list[list[int]], target: int) -> int:
        return solve(mat, target)
