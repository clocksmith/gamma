"""3415. Find Products with Three Consecutive Digits

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(products).
O(total text length + n log n) time; O(total text length + n) transient space.
Requires an isolated maximal ASCII digit run of length three. A longer digit run is never split into triples. A separate longer run does not invalidate a qualifying triple, following the consulted regex solution.
Specification: https://leetcode.com/problems/find-products-with-three-consecutive-digits/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3400-3499/3415.Find%20Products%20with%20Three%20Consecutive%20Digits/README_EN.md
"""

import re

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

def solve(products):
    validate_rows(products, {'product_id': 'int', 'name': 'str'}, ['product_id'])
    return sorted([
        {"product_id": row["product_id"], "name": row["name"]}
        for row in products if any(len(run) == 3 for run in re.findall(r"[0-9]+", row["name"]))
    ], key=lambda row: row["product_id"])
