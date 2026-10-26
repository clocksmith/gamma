"""3436. Find Valid Emails

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(users).
O(total text length + n log n) time; O(n) output space.
Nonempty ASCII local part and alphabetic domain; exactly one @; literal lowercase .com suffix; full-string matching rejects terminal newline tricks.
Specification: https://leetcode.com/problems/find-valid-emails/description/
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

def solve(users):
    validate_rows(users, {'user_id': 'int', 'email': 'str'}, ['user_id'])
    return sorted([
        {"user_id": row["user_id"], "email": row["email"]}
        for row in users if re.fullmatch(r"[A-Za-z0-9_]+@[A-Za-z]+\.com", row["email"])
    ], key=lambda row: row["user_id"])
