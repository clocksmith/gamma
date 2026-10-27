"""603. Consecutive Available Seats. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. cinema: seat_id, free (0/1 or boolean). Output: seat_id in ascending order."""

def solve(cinema):
    free = {row['seat_id'] for row in cinema if row['free'] == 1}
    return [{'seat_id': seat} for seat in sorted(free) if seat - 1 in free or seat + 1 in free]


class Solution:
    def consecutiveSeats(self, cinema):
        return solve(cinema)
