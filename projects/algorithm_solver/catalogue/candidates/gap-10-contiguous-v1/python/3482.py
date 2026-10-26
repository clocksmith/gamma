"""3482. Analyze Organization Hierarchy

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(employees).
O(n log n) time including result sorting; O(n) space.
Uses iterative traversal and bottom-up accumulation. Leaves have team_size 0 and their own salary as budget. Malformed hierarchies reject rather than loop.
Specification: https://leetcode.com/problems/analyze-organization-hierarchy/description/
"""

import re

def checked_integer(value):
    if not -9007199254740991 <= value <= 9007199254740991:
        raise OverflowError("Integer result exceeds the mock JSON safe-integer domain.")
    return value

def validate_rows(rows, schema, primary_key):
    if not isinstance(rows, list):
        raise TypeError("Expected a table as a list of row dictionaries.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Expected a row dictionary.")
        for column, declared in schema.items():
            if column not in row:
                raise TypeError("Missing column: " + column)
            value = row[column]
            if value is None and declared.endswith("?"):
                continue
            kind = declared.rstrip("?")
            valid = False
            if kind == "int":
                valid = type(value) is int and -9007199254740991 <= value <= 9007199254740991
            elif kind == "str":
                valid = isinstance(value, str) and not any(0xD800 <= ord(c) <= 0xDFFF for c in value)
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(employees):
    validate_rows(employees, {'employee_id': 'int', 'employee_name': 'str', 'manager_id': 'int?', 'salary': 'int', 'department': 'str'}, ['employee_id'])
    if not employees:
        return []
    by_id = {row["employee_id"]: row for row in employees}
    children = {row["employee_id"]: [] for row in employees}
    roots = []
    for row in employees:
        if row["manager_id"] is None:
            roots.append(row["employee_id"])
        else:
            if row["manager_id"] not in by_id:
                raise ValueError("Manager does not exist.")
            children[row["manager_id"]].append(row["employee_id"])
    if len(roots) != 1:
        raise ValueError("Expected exactly one CEO.")
    order = [roots[0]]
    level = {roots[0]: 1}
    for manager in order:
        for child in children[manager]:
            if child in level:
                raise ValueError("Cyclic organization.")
            level[child] = level[manager] + 1
            order.append(child)
    if len(order) != len(employees):
        raise ValueError("Organization is cyclic or disconnected.")
    sizes = {}
    budgets = {}
    for employee in reversed(order):
        sizes[employee] = sum(1 + sizes[child] for child in children[employee])
        budgets[employee] = by_id[employee]["salary"] + sum(budgets[child] for child in children[employee])
    result = [
        {"employee_id": row["employee_id"], "employee_name": row["employee_name"],
         "level": level[row["employee_id"]], "team_size": sizes[row["employee_id"]],
         "budget": checked_integer(budgets[row["employee_id"]])}
        for row in employees
    ]
    return sorted(result, key=lambda row: (row["level"], -row["budget"], row["employee_name"], row["employee_id"]))
