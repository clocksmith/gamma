"""4080. Design Bus Seat Booking System.

Specification: https://leetcode.com/problems/design-bus-seat-booking-system/description/
O(1) operations after parsing a seat identifier; O(n) storage. Each active booking retains its original cost.
Retains mutable state on each returned instance; inputs are not modified.
"""

from __future__ import annotations


class BusBooking:
    def __init__(self, n: int):
        self.costs = bytearray(4 * n)
        self.total = 0
        self.count = 0

    def toggle(self, seat: str) -> None:
        column = ord(seat[0]) - ord('A')
        row = int(seat[1:]) - 1
        index = 4 * row + column
        if self.costs[index]:
            self.total -= self.costs[index]
            self.costs[index] = 0
            self.count -= 1
        else:
            cost = 1
            if column == 0 and self.costs[index + 1]:
                cost = 3
            if column == 3 and self.costs[index - 1]:
                cost = 3
            self.costs[index] = cost
            self.total += cost
            self.count += 1

    def getTotalTime(self) -> int:
        return self.total

    def getMinTime(self) -> int:
        return self.count


def solve(n: int) -> BusBooking:
    return BusBooking(n)
