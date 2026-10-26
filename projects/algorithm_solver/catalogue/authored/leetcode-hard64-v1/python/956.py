"""956. Tallest Billboard: difference dynamic programming retaining the greatest shorter support."""


def solve(rods: list[int]) -> int:
    """O(n * S) time and O(S) space, S = sum of rods. Inputs are preserved."""
    states = {0: 0}
    for rod in rods:
        following = dict(states)
        for difference, shorter in states.items():
            larger_difference = difference + rod
            following[larger_difference] = max(following.get(larger_difference, 0), shorter)
            balanced_difference = abs(difference - rod)
            balanced_height = shorter + min(difference, rod)
            following[balanced_difference] = max(following.get(balanced_difference, 0), balanced_height)
        states = following
    return states[0]


class Solution:
    def tallestBillboard(self, rods: list[int]) -> int:
        return solve(rods)
