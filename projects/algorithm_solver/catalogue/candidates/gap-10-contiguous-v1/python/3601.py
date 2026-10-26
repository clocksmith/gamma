"""3601. Find Drivers with Improved Fuel Efficiency

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(drivers, trips).
O(trips + drivers + output log output) rational operations; O(drivers) rational state. Exact fraction arithmetic has operand-size-dependent cost.
Uses the arithmetic mean of trip efficiencies, not a ratio of summed distance/fuel. Filters positive improvement before rounding; sorts by the displayed rounded improvement. Half-year groups pool all supplied dates, without inventing a year column. Undefined zero-fuel ratios are ignored.
Specification: https://leetcode.com/problems/find-drivers-with-improved-fuel-efficiency/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3601.Find%20Drivers%20with%20Improved%20Fuel%20Efficiency/README_EN.md
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

def solve(drivers, trips):
    validate_rows(drivers, {'driver_id': 'int', 'driver_name': 'str'}, ['driver_id'])
    validate_rows(trips, {'trip_id': 'int', 'driver_id': 'int', 'trip_date': 'date', 'distance_km': 'decimal', 'fuel_consumed': 'decimal'}, ['trip_id'])
    groups = {}
    for trip in trips:
        fuel = decimal(trip["fuel_consumed"])
        # SQL division by zero gives NULL, which AVG does not count.
        if fuel == 0:
            continue
        halves = groups.setdefault(trip["driver_id"], [[Fraction(0), 0], [Fraction(0), 0]])
        half = 0 if int(trip["trip_date"][5:7]) <= 6 else 1
        halves[half][0] += decimal(trip["distance_km"]) / fuel
        halves[half][1] += 1
    result = []
    for driver in drivers:
        halves = groups.get(driver["driver_id"])
        if halves is None or not halves[0][1] or not halves[1][1]:
            continue
        first = halves[0][0] / halves[0][1]
        second = halves[1][0] / halves[1][1]
        improvement = second - first
        if improvement <= 0:
            continue
        row = {"driver_id": driver["driver_id"], "driver_name": driver["driver_name"],
               "first_half_avg": rounded_text(first), "second_half_avg": rounded_text(second),
               "efficiency_improvement": rounded_text(improvement)}
        result.append((-rounded_units(improvement), driver["driver_name"], driver["driver_id"], row))
    result.sort(key=lambda item: item[:3])
    return [item[3] for item in result]
