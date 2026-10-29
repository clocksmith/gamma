"""Original frontend 587 variant; qualification unknown."""


def _cross(o, a, b) -> int:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def solve(trees):
    pts = sorted((p[0], p[1]) for p in trees)
    if len(pts) <= 3:
        return [[x, y] for x, y in pts]
    lower = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) < 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) < 0:
            upper.pop()
        upper.append(p)
    hull = sorted(set(lower + upper))
    return [[x, y] for x, y in hull]


outerTrees = solve


class Solution:
    def outerTrees(self, trees):
        return solve(trees)
