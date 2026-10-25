class Solution:
    def minMovesToSeat(self, seats: list[int], students: list[int]) -> int:
        ordered_seats = sorted(seats)
        ordered_students = sorted(students)
        total = 0
        for seat, student in zip(ordered_seats, ordered_students):
            total += abs(seat - student)
        return total
