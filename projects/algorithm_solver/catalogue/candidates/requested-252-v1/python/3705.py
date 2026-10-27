"""3705. Find Golden Hour Customers
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(restaurant_orders).
Algorithm: Per-customer exact count/rating aggregation with inclusive time-of-day peak windows.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Safe JSON integer inputs; exact Python integer / JavaScript BigInt aggregates and ratios. Rounded decimal outputs are fixed-point strings with half-away-from-zero rounding; integer outputs stay numbers.
Mutation: Input tables and row objects remain unchanged; output rows are fresh objects.
Interface: Proposed mock-relations/v1: synchronous solve(tableRows), list of dictionaries / array of objects with original SQL column names. Not native Pandas, a SQL engine, Mox, or a qualified Gamma adapter.
Specification: https://leetcode.com/problems/find-golden-hour-customers/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3705.Find%20Golden%20Hour%20Customers/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Peak windows include exactly 11:00:00..14:00:00 and 18:00:00..21:00:00, not whole terminal hours. Display percentage is rounded to an integer, matching the consulted SQL output; average rating is a 2-decimal string. Eligibility uses unrounded average >=4, unlike the mirror's rounded-alias filter. Sorting uses rounded displayed rating then customer_id descending.
"""

from datetime import date
import math
import re


_SAFE_INTEGER = 9007199254740991


def _date_day(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError("Expected normalized Gregorian YYYY-MM-DD.")
    parsed = date.fromisoformat(value)
    return (parsed - date(1970, 1, 1)).days


def _timestamp_seconds(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", value) is None:
        raise ValueError("Expected YYYY-MM-DD HH:MM:SS without timezone or fractional seconds.")
    hour, minute, second = map(int, value[11:].split(":"))
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError("Invalid timestamp clock.")
    return _date_day(value[:10]) * 86400 + hour * 3600 + minute * 60 + second


def _decimal_parts(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise TypeError("Expected a decimal string or finite number.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite decimal.")
    text = str(value)
    if len(text) > 1024:
        raise ValueError("Decimal text exceeds the adapter bound.")
    match = re.fullmatch(r"([+-]?)([0-9]+)(?:\.([0-9]*))?(?:[eE]([+-]?[0-9]+))?", text)
    if match is None:
        raise ValueError("Invalid decimal.")
    sign, integral, fractional, exponent_text = match.groups()
    fractional = fractional or ""
    exponent = int(exponent_text or "0")
    if abs(exponent) > 1000:
        raise ValueError("Decimal exponent exceeds the adapter bound.")
    coefficient = int(integral + fractional)
    if sign == "-":
        coefficient = -coefficient
    scale = len(fractional) - exponent
    if scale < 0:
        coefficient *= 10 ** (-scale)
        scale = 0
    return coefficient, scale


def _decimal_text(coefficient, scale):
    if coefficient == 0:
        return "0"
    negative = coefficient < 0
    digits = str(abs(coefficient))
    if scale:
        digits = digits.zfill(scale + 1)
        text = digits[:-scale] + "." + digits[-scale:]
        text = text.rstrip("0").rstrip(".")
    else:
        text = digits
    return ("-" if negative else "") + text


def _rounded_units(numerator, denominator, places=2):
    if denominator <= 0:
        raise ValueError("Expected positive denominator.")
    negative = numerator < 0
    quotient, remainder = divmod(abs(numerator) * 10 ** places, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return -quotient if negative else quotient


def _fixed_text(units, places=2):
    negative = units < 0
    digits = str(abs(units)).zfill(places + 1)
    text = digits[:-places] + "." + digits[-places:] if places else digits
    return ("-" if negative else "") + text


def _check_table(rows, schema, primary_key):
    if not isinstance(rows, list):
        raise TypeError("Expected a list of row dictionaries.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("Expected a row dictionary.")
        for column, declared in schema.items():
            if column not in row:
                raise ValueError("Missing column: " + column)
            value = row[column]
            if value is None and declared.endswith("?"):
                continue
            kind = declared.rstrip("?")
            if kind == "int":
                if isinstance(value, bool) or not isinstance(value, int) or abs(value) > _SAFE_INTEGER:
                    raise TypeError("Expected a safe JSON integer: " + column)
            elif kind == "str":
                if not isinstance(value, str) or any(0xD800 <= ord(character) <= 0xDFFF for character in value):
                    raise TypeError("Expected a Unicode scalar string: " + column)
            elif kind == "date":
                _date_day(value)
            elif kind == "datetime":
                _timestamp_seconds(value)
            elif kind == "decimal":
                _decimal_parts(value)
            else:
                raise ValueError("Unknown adapter schema type.")
        identity = tuple(row[column] for column in primary_key)
        if identity in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(identity)


def solve(restaurant_orders):
    _check_table(restaurant_orders, {"order_id": "int", "customer_id": "int", "order_timestamp": "datetime", "order_amount": "decimal", "payment_method": "str", "order_rating": "int?"}, ("order_id",))
    groups = {}
    for row in restaurant_orders:
        if row["payment_method"] not in ("cash", "card", "app"):
            raise ValueError("Unknown payment method.")
        rating = row["order_rating"]
        if rating is not None and not 1 <= rating <= 5:
            raise ValueError("Rating must be 1..5 or null.")
        seconds = _timestamp_seconds(row["order_timestamp"]) % 86400
        peak = 11 * 3600 <= seconds <= 14 * 3600 or 18 * 3600 <= seconds <= 21 * 3600
        stats = groups.setdefault(row["customer_id"], [0, 0, 0, 0])
        stats[0] += 1
        stats[1] += peak
        if rating is not None:
            stats[2] += 1
            stats[3] += rating
    result = []
    for customer, (total, peak, rated, rating_sum) in groups.items():
        if total >= 3 and 5 * peak >= 3 * total and 2 * rated >= total and rated and rating_sum >= 4 * rated:
            average = _rounded_units(rating_sum, rated)
            result.append((average, customer, {"customer_id": customer, "total_orders": total,
                "peak_hour_percentage": _rounded_units(100 * peak, total, 0),
                "average_rating": _fixed_text(average)}))
    result.sort(key=lambda item: (-item[0], -item[1]))
    return [item[2] for item in result]
