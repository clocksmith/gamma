"""1109. Corporate Flight Bookings (Medium).

Specification: https://leetcode.com/problems/corporate-flight-bookings/description/
"""


def solve(bookings: list[list[int]], n: int) -> list[int]:
    diff = [0] * (n + 1)
    for first, last, seats in bookings:
        diff[first - 1] += seats
        if last < n:
            diff[last] -= seats
    result = []
    current = 0
    for i in range(n):
        current += diff[i]
        result.append(current)
    return result


class Solution:
    def corpFlightBookings(self, bookings: list[list[int]], n: int) -> list[int]:
        return solve(bookings, n)
