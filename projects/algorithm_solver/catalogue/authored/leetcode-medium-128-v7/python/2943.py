"""2943. Maximize Area of Square Hole in Grid: find consecutive removable-bar runs on both axes and use the smaller opening."""


def solve(n: int, m: int, hBars: list[int], vBars: list[int]) -> int:
    """O(h log h + v log v) time and O(h + v) auxiliary space; inputs are read-only."""
    def opening(bars: list[int]) -> int:
        longest = run = 0
        previous = None
        for bar in sorted(bars):
            run = run + 1 if previous is not None and bar == previous + 1 else 1
            longest = max(longest, run)
            previous = bar
        return longest + 1

    side = min(opening(hBars), opening(vBars))
    return side * side


class Solution:
    def maximizeSquareHoleArea(self, n: int, m: int, hBars: list[int], vBars: list[int]) -> int:
        return solve(n, m, hBars, vBars)
