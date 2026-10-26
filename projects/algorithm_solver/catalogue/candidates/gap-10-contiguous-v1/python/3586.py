"""3586. Find COVID Recovery Patients

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(patients, covidTests).
O(tests + patients + output log output) time; O(patients with test results) space.
Finds the first negative strictly after the first positive, not the overall first negative. Calendar-day arithmetic is timezone-independent. This is a database exercise, not medical guidance.
Specification: https://leetcode.com/problems/find-covid-recovery-patients/description/
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

def solve(patients, covidTests):
    validate_rows(patients, {'patient_id': 'int', 'patient_name': 'str', 'age': 'int'}, ['patient_id'])
    validate_rows(covidTests, {'test_id': 'int', 'patient_id': 'int', 'test_date': 'date', 'result': 'str'}, ['test_id'])
    first_positive = {}
    for row in covidTests:
        if row["result"] not in ("Positive", "Negative", "Inconclusive"):
            raise ValueError("Unknown COVID-test result.")
        patient_id = row["patient_id"]
        if row["result"] == "Positive" and (patient_id not in first_positive or row["test_date"] < first_positive[patient_id]):
            first_positive[patient_id] = row["test_date"]
    first_negative = {}
    for row in covidTests:
        patient_id = row["patient_id"]
        if (row["result"] == "Negative" and patient_id in first_positive
                and row["test_date"] > first_positive[patient_id]
                and (patient_id not in first_negative or row["test_date"] < first_negative[patient_id])):
            first_negative[patient_id] = row["test_date"]
    result = [
        {"patient_id": row["patient_id"], "patient_name": row["patient_name"], "age": row["age"],
         "recovery_time": day_index(first_negative[row["patient_id"]]) - day_index(first_positive[row["patient_id"]])}
        for row in patients if row["patient_id"] in first_negative
    ]
    return sorted(result, key=lambda row: (row["recovery_time"], row["patient_name"], row["patient_id"]))
