"""613. Shortest Distance in a Line. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. point: x (unique). Output: shortest; no pair yields NULL."""

def solve(point):
    values = sorted(row['x'] for row in point)
    return [{'shortest': min((values[i] - values[i - 1] for i in range(1, len(values))), default=None)}]


class Solution:
    def shortestDistance(self, point):
        return solve(point)
