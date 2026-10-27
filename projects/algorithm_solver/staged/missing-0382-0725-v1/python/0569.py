"""569. Median Employee Salary. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, company, salary. Output retains one or two middle employee rows per company, breaking equal salaries by id."""

def solve(employee):
    groups = {}
    for row in employee:
        groups.setdefault(row['company'], []).append(row)
    result = []
    for company in sorted(groups):
        rows = sorted(groups[company], key=lambda row: (row['salary'], row['id']))
        size = len(rows)
        for index in range((size - 1) // 2, size // 2 + 1):
            row = rows[index]
            result.append({'id': row['id'], 'company': company, 'salary': row['salary']})
    return result


class Solution:
    def medianEmployeeSalary(self, employee):
        return solve(employee)
