"""610. Triangle Judgement. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. triangle: x, y, z. Output: x, y, z, triangle."""

def solve(triangle):
    return [{'x': row['x'], 'y': row['y'], 'z': row['z'],
             'triangle': 'Yes' if row['x'] + row['y'] > row['z'] and row['x'] + row['z'] > row['y'] and row['y'] + row['z'] > row['x'] else 'No'}
            for row in triangle]


class Solution:
    def triangleJudgement(self, triangle):
        return solve(triangle)
