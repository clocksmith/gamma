"""3657. Find Loyal Customers
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(customer_transactions).
Algorithm: Aggregate purchase/refund counts and activity span per customer; apply exact ratio inequalities.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Safe JSON integer inputs; exact Python integer / JavaScript BigInt aggregates and ratios. Rounded decimal outputs are fixed-point strings with half-away-from-zero rounding; integer outputs stay numbers.
Mutation: Input tables and row objects remain unchanged; output rows are fresh objects.
Interface: Proposed mock-relations/v1: synchronous solve(tableRows), list of dictionaries / array of objects with original SQL column names. Not native Pandas, a SQL engine, Mox, or a qualified Gamma adapter.
Specification: https://leetcode.com/problems/find-loyal-customers/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3657.Find%20Loyal%20Customers/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Activity span includes all transactions. Refund ratio is refund count / all transaction count, not refunded money / purchased money. At least 30 elapsed calendar days; ratio strictly below 20%.
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


def solve(customer_transactions):
    _check_table(customer_transactions, {"transaction_id": "int", "customer_id": "int", "transaction_date": "date", "amount": "decimal", "transaction_type": "str"}, ("transaction_id",))
    groups = {}
    for row in customer_transactions:
        kind = row["transaction_type"]
        if kind not in ("purchase", "refund"):
            raise ValueError("Unknown transaction type.")
        day = _date_day(row["transaction_date"])
        stats = groups.setdefault(row["customer_id"], [0, 0, 0, day, day])
        stats[0] += 1
        stats[1] += kind == "purchase"
        stats[2] += kind == "refund"
        stats[3] = min(stats[3], day)
        stats[4] = max(stats[4], day)
    return [{"customer_id": customer} for customer, stats in sorted(groups.items())
            if stats[1] >= 3 and 5 * stats[2] < stats[0] and stats[4] - stats[3] >= 30]
