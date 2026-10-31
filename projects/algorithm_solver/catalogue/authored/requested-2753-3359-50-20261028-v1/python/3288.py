"""Original frontend 3288 variant; qualification unknown."""

import bisect


def solve(coordinates, k: int) -> int:
    xk, yk = coordinates[k]
    left = [(x, y) for x, y in coordinates if x < xk and y < yk]
    right = [(x, y) for x, y in coordinates if x > xk and y > yk]

    def lis_2d(pts) -> int:
        pts.sort(key=lambda p: (p[0], -p[1]))
        tails = []
        for _, y in pts:
            idx = bisect.bisect_left(tails, y)
            if idx == len(tails):
                tails.append(y)
            else:
                tails[idx] = y
        return len(tails)

    return 1 + lis_2d(left) + lis_2d(right)


maxPathLength = solve


class Solution:
    def maxPathLength(self, coordinates, k: int) -> int:
        return solve(coordinates, k)
