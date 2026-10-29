"""Original frontend 765 variant; qualification unknown."""

def solve(row):
    seats = row[:]
    where = [0] * len(seats)
    for seat, person in enumerate(seats):
        where[person] = seat
    swaps = 0
    for seat in range(0, len(seats), 2):
        partner = seats[seat] ^ 1
        if seats[seat + 1] != partner:
            other = where[partner]
            seats[other] = seats[seat + 1]
            where[seats[other]] = other
            seats[seat + 1] = partner
            where[partner] = seat + 1
            swaps += 1
    return swaps


class Solution:
    def minSwapsCouples(self, row):
        return solve(row)
