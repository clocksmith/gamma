class Solution:
    def corpFlightBookings(self, bookings: list[list[int]], n: int) -> list[int]:
        changes = [0] * (n + 1)
        for first, last, seats in bookings:
            changes[first - 1] += seats
            changes[last] -= seats
        output = []
        active = 0
        for index in range(n):
            active += changes[index]
            output.append(active)
        return output
