"""615. Average Salary: Departments VS Company. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. salary: id, employee_id, amount (integer), pay_date (YYYY-MM-DD or YYYY/MM/DD); employee: employee_id, department_id. Output: pay_month, department_id, comparison. Compares exact cross-products instead of rounded averages."""

def solve(salary, employee):
    department = {row['employee_id']: row['department_id'] for row in employee}
    company, groups = {}, {}
    for row in salary:
        month = row['pay_date'].replace('/', '-')[:7]
        amount = row['amount']
        total = company.setdefault(month, [0, 0])
        group = groups.setdefault((month, department[row['employee_id']]), [0, 0])
        if amount is not None:
            total[0] += amount
            total[1] += 1
            group[0] += amount
            group[1] += 1
    result = []
    for (month, dept), (subtotal, count) in sorted(groups.items()):
        total, company_count = company[month]
        difference = subtotal * company_count - total * count
        comparison = 'same' if count == 0 or company_count == 0 or difference == 0 else 'higher' if difference > 0 else 'lower'
        result.append({'pay_month': month, 'department_id': dept, 'comparison': comparison})
    return result


class Solution:
    def averageSalary(self, salary, employee):
        return solve(salary, employee)
