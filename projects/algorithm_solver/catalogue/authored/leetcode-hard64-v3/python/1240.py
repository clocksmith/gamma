"""1240. Tiling a Rectangle with the Fewest Squares: skyline branch-and-bound with reflected-state memoization; exponential worst-case search."""


def solve(n: int, m: int) -> int:
    height, width = max(n, m), min(n, m)
    skyline = [0] * width
    best = height * width
    seen = {}

    def search(used: int) -> None:
        nonlocal best
        if used >= best:
            return
        level = min(skyline)
        if level == height:
            best = used
            return
        state = tuple(skyline)
        state = min(state, state[::-1])
        if seen.get(state, best) <= used:
            return
        seen[state] = used
        left = skyline.index(level)
        right = left
        while right < width and skyline[right] == level:
            right += 1
        maximum = min(right - left, height - level)
        for side in range(maximum, 0, -1):
            for column in range(left, left + side):
                skyline[column] += side
            search(used + 1)
            for column in range(left, left + side):
                skyline[column] -= side

    search(0)
    return best


class Solution:
    def tilingRectangle(self, n: int, m: int) -> int:
        return solve(n, m)
