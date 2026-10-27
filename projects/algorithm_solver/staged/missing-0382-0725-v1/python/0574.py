"""574. Winning Candidate. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. candidate: id, name; vote: id, candidateId. Output: name. The statement guarantees a unique winner."""

def solve(candidate, vote):
    counts = {}
    for row in vote:
        key = row['candidateId']
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return []
    winner = min(counts, key=lambda key: (-counts[key], key))
    return [{'name': row['name']} for row in candidate if row['id'] == winner]


class Solution:
    def winningCandidate(self, candidate, vote):
        return solve(candidate, vote)
