"""3421. Find Students Who Improved

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(scores).
O(exams + groups log groups) time; O(groups) space.
Compares earliest and latest exams per student/subject, not adjacent improvements or score extrema.
Specification: https://leetcode.com/problems/find-students-who-improved/description/
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

def solve(scores):
    validate_rows(scores, {'student_id': 'int', 'subject': 'str', 'score': 'int', 'exam_date': 'date'}, ['student_id', 'subject', 'exam_date'])
    groups = {}
    for row in scores:
        key = (row["student_id"], row["subject"])
        if key not in groups:
            groups[key] = {"first": row, "latest": row, "count": 0}
        group = groups[key]
        group["count"] += 1
        if row["exam_date"] < group["first"]["exam_date"]:
            group["first"] = row
        if row["exam_date"] > group["latest"]["exam_date"]:
            group["latest"] = row
    result = []
    for (student, subject), group in groups.items():
        if group["count"] >= 2 and group["latest"]["score"] > group["first"]["score"]:
            result.append({"student_id": student, "subject": subject,
                           "first_score": group["first"]["score"], "latest_score": group["latest"]["score"]})
    return sorted(result, key=lambda row: (row["student_id"], row["subject"]))
