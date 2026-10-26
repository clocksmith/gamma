"""2938. Separate Black and White Balls: count each one-before-zero inversion as one required adjacent swap."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    ones = steps = 0
    for character in s:
        if character == '1':
            ones += 1
        else:
            steps += ones
    return steps


class Solution:
    def minimumSteps(self, s: str) -> int:
        return solve(s)
