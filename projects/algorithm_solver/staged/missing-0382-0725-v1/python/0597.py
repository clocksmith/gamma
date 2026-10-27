"""597. Friend Requests I: Overall Acceptance Rate. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. friend_request: sender_id, send_to_id, request_date; request_accepted: requester_id, accepter_id, accept_date. Output: accept_rate. Deduplicates each table independently, without intersecting pairs."""

from decimal import Decimal, ROUND_HALF_UP, localcontext


def _rounded_ratio(numerator, denominator, places):
    with localcontext() as context:
        context.prec = 60
        value = Decimal(numerator) / Decimal(denominator)
        return float(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

def solve(friend_request, request_accepted):
    requests = {(row['sender_id'], row['send_to_id']) for row in friend_request}
    accepted = {(row['requester_id'], row['accepter_id']) for row in request_accepted}
    return [{'accept_rate': _rounded_ratio(len(accepted), len(requests), 2) if requests else 0.0}]


class Solution:
    def acceptanceRate(self, friend_request, request_accepted):
        return solve(friend_request, request_accepted)
