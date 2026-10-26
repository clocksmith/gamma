"""2037. Minimum Number of Moves to Seat Everyone (Easy).

Specification: https://leetcode.com/problems/minimum-number-of-moves-to-seat-everyone/description/
"""


def solve(seats: list[int], students: list[int]) -> int:
    """O(n log n) time, O(n) space; pair both sorted copies in order."""
    ordered_seats = sorted(seats)
    ordered_students = sorted(students)
    return sum(abs(seat - student) for seat, student in zip(ordered_seats, ordered_students))


class Solution:
    def minMovesToSeat(self, seats: list[int], students: list[int]) -> int:
        return solve(seats, students)
