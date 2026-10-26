"""2211. Count Collisions on a Road: discard cars escaping outward and count every moving car left inside."""


def solve(directions: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    left, right = 0, len(directions) - 1
    while left <= right and directions[left] == 'L':
        left += 1
    while left <= right and directions[right] == 'R':
        right -= 1
    return sum(directions[index] != 'S' for index in range(left, right + 1))


class Solution:
    def countCollisions(self, directions: str) -> int:
        return solve(directions)
