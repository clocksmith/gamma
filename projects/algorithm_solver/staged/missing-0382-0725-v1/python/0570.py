"""570. Managers with at Least 5 Direct Reports. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, name, department, managerId (nullable). Output: name."""

def solve(employee):
    counts = {}
    for row in employee:
        manager = row['managerId']
        if manager is not None:
            counts[manager] = counts.get(manager, 0) + 1
    return [{'name': row['name']} for row in employee if counts.get(row['id'], 0) >= 5]


class Solution:
    def findManagers(self, employee):
        return solve(employee)
