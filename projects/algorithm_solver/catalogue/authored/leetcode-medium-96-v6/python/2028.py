"""2028. Find Missing Observations: distribute the required missing sum as evenly as possible."""


def solve(rolls: list[int], mean: int, n: int) -> list[int]:
    """O(m + n) time and O(n) result space; inputs are read-only."""
    missing = mean * (len(rolls) + n) - sum(rolls)
    if missing < n or missing > 6 * n:
        return []
    value, extra = divmod(missing, n)
    return [value + (index < extra) for index in range(n)]


class Solution:
    def missingRolls(self, rolls: list[int], mean: int, n: int) -> list[int]:
        return solve(rolls, mean, n)
