"""957. Prison Cells After N Days (Medium).

Specification: https://leetcode.com/problems/prison-cells-after-n-days/description/
"""


def _next_day(cells):
    nxt = [0] * 8
    for i in range(1, 7):
        nxt[i] = 1 if cells[i - 1] == cells[i + 1] else 0
    return nxt


def solve(cells: list[int], n: int) -> list[int]:
    seen = {}
    current = cells[:]
    day = 0
    while day < n:
        key = tuple(current)
        if key in seen:
            cycle = day - seen[key]
            remaining = (n - day) % cycle
            for _i in range(remaining):
                current = _next_day(current)
            return current
        seen[key] = day
        current = _next_day(current)
        day += 1
    return current


class Solution:
    def prisonAfterNDays(self, cells: list[int], n: int) -> list[int]:
        return solve(cells, n)
