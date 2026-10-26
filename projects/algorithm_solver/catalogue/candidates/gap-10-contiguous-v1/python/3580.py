"""3580. Find Consistently Improving Employees

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(employees, performanceReviews).
O(reviews log reviews + employees + output log output) time; O(reviews) space.
Only the most recent three reviews count. Equal review dates are ordered by review_id as a declared mock tie rule; the public wording does not independently qualify that tie rule.
Specification: https://leetcode.com/problems/find-consistently-improving-employees/description/
"""

import re
from datetime import date

def day_index(value):
    if not isinstance(value, str) or len(value) != 10 or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise TypeError("Expected a Gregorian YYYY-MM-DD date.")
    return date.fromisoformat(value).toordinal()

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
            elif kind == "date":
                day_index(value)
                valid = True
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(employees, performanceReviews):
    validate_rows(employees, {'employee_id': 'int', 'name': 'str'}, ['employee_id'])
    validate_rows(performanceReviews, {'review_id': 'int', 'employee_id': 'int', 'review_date': 'date', 'rating': 'int'}, ['review_id'])
    grouped = {}
    for row in performanceReviews:
        grouped.setdefault(row["employee_id"], []).append(row)
    result = []
    for employee in employees:
        reviews = sorted(grouped.get(employee["employee_id"], []),
                         key=lambda row: (row["review_date"], row["review_id"]), reverse=True)
        if len(reviews) >= 3 and reviews[0]["rating"] > reviews[1]["rating"] > reviews[2]["rating"]:
            result.append({"employee_id": employee["employee_id"], "name": employee["name"],
                           "improvement_score": reviews[0]["rating"] - reviews[2]["rating"]})
    return sorted(result, key=lambda row: (-row["improvement_score"], row["name"], row["employee_id"]))
