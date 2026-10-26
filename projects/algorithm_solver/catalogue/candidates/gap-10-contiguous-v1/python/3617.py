"""3617. Find Students with Study Spiral Pattern

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(students, studySessions).
O(sessions log sessions + students + output log output) rational operations; O(sessions) space.
Explicit interpretation from the pinned reference: the entire ordered student history must be complete repetitions of its distinct-subject cycle, with no gap over two days. No search for a qualifying subwindow; incomplete final cycles reject. Same-date sessions use session_id ascending. These choices require Gamma contract approval.
Specification: https://leetcode.com/problems/find-students-with-study-spiral-pattern/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3617.Find%20Students%20with%20Study%20Spiral%20Pattern/README_EN.md
"""

import re
from datetime import date
import math
from fractions import Fraction

def day_index(value):
    if not isinstance(value, str) or len(value) != 10 or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise TypeError("Expected a Gregorian YYYY-MM-DD date.")
    return date.fromisoformat(value).toordinal()

def decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise TypeError("Expected a finite decimal number or decimal string.")
    if isinstance(value, float) and not math.isfinite(value):
        raise TypeError("Expected a finite decimal number or decimal string.")
    text = str(value)
    match = re.fullmatch(r"([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?", text)
    if match is None or len(text) > 1024:
        raise TypeError("Invalid mock decimal representation.")
    fraction = match.group(3) or ""
    exponent = int(match.group(4) or "0") - len(fraction)
    if abs(exponent) > 1000:
        raise ValueError("Mock decimal exponent exceeds the declared bound.")
    numerator = int(match.group(2) + fraction)
    if match.group(1) == "-":
        numerator = -numerator
    return Fraction(numerator * 10 ** exponent) if exponent >= 0 else Fraction(numerator, 10 ** (-exponent))


def rounded_units(value, places=2):
    quotient, remainder = divmod(abs(value.numerator) * 10 ** places, value.denominator)
    if 2 * remainder >= value.denominator:
        quotient += 1
    return -quotient if value < 0 else quotient


def units_text(units, places, trim=False):
    sign = "-" if units < 0 else ""
    digits = str(abs(units))
    if places == 0:
        return sign + digits
    digits = digits.zfill(places + 1)
    text = sign + digits[:-places] + "." + digits[-places:]
    return text.rstrip("0").rstrip(".") if trim else text


def rounded_text(value, places=2):
    return units_text(rounded_units(value, places), places)


def exact_decimal_text(value):
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("Nonterminating decimal requires an explicit rounding rule.")
    places = max(twos, fives)
    return units_text(value.numerator * 10 ** places // value.denominator, places, True)

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
            elif kind == "decimal":
                decimal(value)
                valid = True
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(students, studySessions):
    validate_rows(students, {'student_id': 'int', 'student_name': 'str', 'major': 'str'}, ['student_id'])
    validate_rows(studySessions, {'session_id': 'int', 'student_id': 'int', 'subject': 'str', 'session_date': 'date', 'hours_studied': 'decimal'}, ['session_id'])
    groups = {}
    for session in studySessions:
        groups.setdefault(session["student_id"], []).append(session)
    result = []
    for student in students:
        sessions = sorted(groups.get(student["student_id"], []), key=lambda row: (row["session_date"], row["session_id"]))
        cycle_length = len({row["subject"] for row in sessions})
        if cycle_length < 3 or len(sessions) < 2 * cycle_length or len(sessions) % cycle_length != 0:
            continue
        valid = True
        hours = Fraction(0)
        for index, session in enumerate(sessions):
            if (session["subject"] != sessions[index % cycle_length]["subject"]
                    or (index > 0 and day_index(session["session_date"]) - day_index(sessions[index - 1]["session_date"]) > 2)):
                valid = False
                break
            hours += decimal(session["hours_studied"])
        if valid:
            row = {"student_id": student["student_id"], "student_name": student["student_name"],
                   "major": student["major"], "cycle_length": cycle_length,
                   "total_study_hours": exact_decimal_text(hours)}
            result.append((-cycle_length, -hours, student["student_id"], row))
    result.sort(key=lambda item: item[:3])
    return [item[3] for item in result]
