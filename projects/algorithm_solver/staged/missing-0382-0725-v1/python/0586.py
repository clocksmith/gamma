"""586. Customer Placing the Largest Number of Orders. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. orders: order_number, customer_number. Output: customer_number. The statement guarantees a unique maximum."""

def solve(orders):
    counts = {}
    for row in orders:
        key = row['customer_number']
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return []
    winner = min(counts, key=lambda key: (-counts[key], key))
    return [{'customer_number': winner}]


class Solution:
    def largestOrderCustomer(self, orders):
        return solve(orders)
