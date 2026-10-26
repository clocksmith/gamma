"""3465. Find Products with Valid Serial Numbers

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(products).
O(total description length + n log n) time; O(n) output space.
Case-sensitive SN. Exactly four digits on either side of the hyphen; a fifth trailing digit invalidates that occurrence. No additional word-boundary restriction is invented.
Specification: https://leetcode.com/problems/find-products-with-valid-serial-numbers/description/
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
    validate_rows(products, {'product_id': 'int', 'product_name': 'str', 'description': 'str'}, ['product_id'])
    return sorted([
        {"product_id": row["product_id"], "product_name": row["product_name"], "description": row["description"]}
        for row in products if re.search(r"SN[0-9]{4}-[0-9]{4}(?![0-9])", row["description"])
    ], key=lambda row: row["product_id"])
