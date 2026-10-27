"""550. Game Play Analysis IV. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: fraction; an empty denominator yields NULL."""

from datetime import date

from decimal import Decimal, ROUND_HALF_UP, localcontext


def _rounded_ratio(numerator, denominator, places):
    with localcontext() as context:
        context.prec = 60
        value = Decimal(numerator) / Decimal(denominator)
        return float(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

def solve(activity):
    first, days = {}, set()
    for row in activity:
        player = row['player_id']
        day = date.fromisoformat(row['event_date']).toordinal()
        days.add((player, day))
        first[player] = min(first.get(player, day), day)
    if not first:
        return [{'fraction': None}]
    return [{'fraction': _rounded_ratio(sum((player, day + 1) in days for player, day in first.items()), len(first), 2)}]


class Solution:
    def gamePlayAnalysis(self, activity):
        return solve(activity)
