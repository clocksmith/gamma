"""579. Find Cumulative Salary of an Employee. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, month, salary (one year). Output: id, month, Salary. Uses three calendar months, not three observed records; excludes each latest month."""

def solve(employee):
    groups = {}
    for row in employee:
        groups.setdefault(row['id'], {})[row['month']] = row['salary']
    result = []
    for employee_id in sorted(groups):
        months = groups[employee_id]
        latest = max(months)
        for month in sorted(months, reverse=True):
            if month != latest:
                value = sum(months.get(month - offset, 0) for offset in range(3))
                result.append({'id': employee_id, 'month': month, 'Salary': value})
    return result


class Solution:
    def cumulativeSalary(self, employee):
        return solve(employee)
