"""607. Sales Person. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. sales_person: sales_id, name, salary, commission_rate, hire_date; company: com_id, name, city; orders: order_id, order_date, com_id, sales_id, amount. Output: name."""

def solve(sales_person, company, orders):
    red = {row['com_id'] for row in company if row['name'] == 'RED'}
    excluded = {row['sales_id'] for row in orders if row['com_id'] in red}
    return [{'name': row['name']} for row in sales_person if row['sales_id'] not in excluded]


class Solution:
    def salesPerson(self, sales_person, company, orders):
        return solve(sales_person, company, orders)
