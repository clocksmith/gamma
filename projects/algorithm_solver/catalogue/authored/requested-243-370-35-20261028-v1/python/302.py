"""Original frontend 302 variant; qualification unknown."""


def solve(image, x: int, y: int) -> int:
    r_lo = r_hi = x
    c_lo = c_hi = y
    for r, row in enumerate(image):
        for c, ch in enumerate(row):
            if ch == "1" or ch == 1:
                if r < r_lo:
                    r_lo = r
                if r > r_hi:
                    r_hi = r
                if c < c_lo:
                    c_lo = c
                if c > c_hi:
                    c_hi = c
    return (r_hi - r_lo + 1) * (c_hi - c_lo + 1)


minArea = solve


class Solution:
    def minArea(self, image, x: int, y: int) -> int:
        return solve(image, x, y)
