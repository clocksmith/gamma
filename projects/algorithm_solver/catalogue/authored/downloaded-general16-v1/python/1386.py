"""1386. Cinema Seat Allocation (Medium).

Specification: https://leetcode.com/problems/cinema-seat-allocation/description/
"""


def solve(n, reservedSeats):
    rows = {}
    for row, seat in reservedSeats:
        rows.setdefault(row, set()).add(seat)
    families = (n - len(rows)) * 2
    for seats in rows.values():
        left = not any(seat in seats for seat in (2, 3, 4, 5))
        middle = not any(seat in seats for seat in (4, 5, 6, 7))
        right = not any(seat in seats for seat in (6, 7, 8, 9))
        if left and right:
            families += 2
        elif left or middle or right:
            families += 1
    return families


class Solution:
    def maxNumberOfFamilies(self, n, reservedSeats):
        return solve(n, reservedSeats)
