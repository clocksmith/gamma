"""584. Find Customer Referee. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. customer: id, name, referee_id (nullable). Output: name; NULL referee_id qualifies."""

def solve(customer):
    return [{'name': row['name']} for row in customer if row['referee_id'] != 2]


class Solution:
    def findCustomerReferee(self, customer):
        return solve(customer)
