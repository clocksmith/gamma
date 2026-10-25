"""2860. Happy Students: count valid selection sizes between sorted thresholds."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    values = sorted(nums)
    answer = 1 if values[0] > 0 else 0
    for selected in range(1, len(values) + 1):
        if values[selected - 1] < selected and (selected == len(values) or values[selected] > selected):
            answer += 1
    return answer


class Solution:
    def countWays(self, nums: list[int]) -> int:
        return solve(nums)
