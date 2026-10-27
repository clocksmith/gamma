"""601. Human Traffic of Stadium. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. stadium: id, visit_date (YYYY-MM-DD), people. Output: id, visit_date, people. Consecutiveness uses IDs, not calendar days."""

def solve(stadium):
    qualifying = {row['id'] for row in stadium if row['people'] >= 100}
    result = []
    for row in stadium:
        current = row['id']
        if current in qualifying and ((current - 2 in qualifying and current - 1 in qualifying)
                or (current - 1 in qualifying and current + 1 in qualifying)
                or (current + 1 in qualifying and current + 2 in qualifying)):
            result.append({'id': current, 'visit_date': row['visit_date'], 'people': row['people']})
    return sorted(result, key=lambda row: (row['visit_date'], row['id']))


class Solution:
    def stadiumTraffic(self, stadium):
        return solve(stadium)
