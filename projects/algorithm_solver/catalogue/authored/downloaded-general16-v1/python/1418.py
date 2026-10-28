"""1418. Display Table of Food Orders in a Restaurant (Medium).

Specification: https://leetcode.com/problems/display-table-of-food-orders-in-a-restaurant/description/
"""


def solve(orders):
    foods = set()
    tables = {}
    for customer, table, food in orders:
        foods.add(food)
        counts = tables.setdefault(table, {})
        counts[food] = counts.get(food, 0) + 1
    sorted_foods = sorted(foods)
    header = ["Table"] + sorted_foods
    rows = []
    for table in sorted(tables, key=lambda value: int(value)):
        counts = tables[table]
        rows.append([table] + [str(counts.get(food, 0)) for food in sorted_foods])
    return [header] + rows


class Solution:
    def displayTable(self, orders):
        return solve(orders)
