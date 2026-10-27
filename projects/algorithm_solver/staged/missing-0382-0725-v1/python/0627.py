"""627. Swap Salary. Gamma row-record adapter for a SQL UPDATE, not a native SQL submission. salary rows have id, name, sex, salary. Mutates each original row sex in place and returns the original table; other columns and row identities are preserved."""

def solve(salary):
    for row in salary:
        if row['sex'] == 'm':
            row['sex'] = 'f'
        elif row['sex'] == 'f':
            row['sex'] = 'm'
    return salary


class Solution:
    def swapSalary(self, salary):
        return solve(salary)
