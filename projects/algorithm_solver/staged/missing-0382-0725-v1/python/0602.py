"""602. Friend Requests II: Who Has the Most Friends. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. request_accepted: requester_id, accepter_id, accept_date. Output: id, num. Each accepted pair contributes one friend to each endpoint; maximum is unique in the stated domain."""

def solve(request_accepted):
    counts = {}
    for row in request_accepted:
        for key in (row['requester_id'], row['accepter_id']):
            counts[key] = counts.get(key, 0) + 1
    if not counts:
        return []
    winner = min(counts, key=lambda key: (-counts[key], key))
    return [{'id': winner, 'num': counts[winner]}]


class Solution:
    def mostFriends(self, request_accepted):
        return solve(request_accepted)
