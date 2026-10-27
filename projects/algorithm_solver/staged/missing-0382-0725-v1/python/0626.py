"""626. Exchange Seats. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. seat: id, student; IDs are consecutive from 1. Output: id, student; final unpaired seat remains unchanged."""

def solve(seat):
    rows = sorted(seat, key=lambda row: row['id'])
    result = []
    for i, row in enumerate(rows):
        partner = i + 1 if i % 2 == 0 and i + 1 < len(rows) else i - 1 if i % 2 else i
        result.append({'id': row['id'], 'student': rows[partner]['student']})
    return result


class Solution:
    def exchangeSeats(self, seat):
        return solve(seat)
