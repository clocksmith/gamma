"""3451. Find Invalid IP Addresses

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(logs).
O(total IP length + distinct invalid IPs log count) time; O(distinct invalid IPs) space.
Counts distinct log rows by the original IP string; valid zero octets are allowed, leading-zero multi-digit octets are not.
Specification: https://leetcode.com/problems/find-invalid-ip-addresses/description/
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

def solve(logs):
    validate_rows(logs, {'log_id': 'int', 'ip': 'str', 'status_code': 'int'}, ['log_id'])
    counts = {}
    for row in logs:
        parts = row["ip"].split(".")
        valid = len(parts) == 4 and all(
            re.fullmatch(r"[0-9]{1,3}", part) is not None
            and (len(part) == 1 or part[0] != "0") and int(part) <= 255
            for part in parts
        )
        if not valid:
            counts[row["ip"]] = counts.get(row["ip"], 0) + 1
    return sorted([{"ip": ip, "invalid_count": count} for ip, count in counts.items()],
                  key=lambda row: (row["invalid_count"], row["ip"]), reverse=True)
