"""577. Employee Bonus. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: empId, name, supervisor, salary; bonus: empId, bonus. Output: name, bonus; missing bonuses remain NULL."""

def solve(employee, bonus):
    bonuses = {row['empId']: row['bonus'] for row in bonus}
    result = []
    for row in employee:
        value = bonuses.get(row['empId'])
        if value is None or value < 1000:
            result.append({'name': row['name'], 'bonus': value})
    return result


class Solution:
    def employeeBonus(self, employee, bonus):
        return solve(employee, bonus)
