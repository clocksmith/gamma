"""2929. Distribute Candies Among Children II: exclude children exceeding their limit from the unconstrained three-way compositions."""


def solve(n: int, limit: int) -> int:
    """O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only."""
    def unrestricted(total: int) -> int:
        return (total + 1) * (total + 2) // 2 if total >= 0 else 0

    step = limit + 1
    return (unrestricted(n) - 3 * unrestricted(n - step)
            + 3 * unrestricted(n - 2 * step) - unrestricted(n - 3 * step))


class Solution:
    def distributeCandies(self, n: int, limit: int) -> int:
        return solve(n, limit)
