"""3716. Find Churn Risk Customers
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(subscription_events).
Algorithm: Sort each user's event history; compare final active amount with exact historical maximum and first-to-last duration.
Complexity: O(n log n) time; O(n) space.
Numeric semantics: Safe JSON integer inputs; exact Python integer / JavaScript BigInt aggregates and ratios. Rounded decimal outputs are fixed-point strings with half-away-from-zero rounding; integer outputs stay numbers.
Mutation: Input tables and row objects remain unchanged; output rows are fresh objects.
Interface: Proposed mock-relations/v1: synchronous solve(tableRows), list of dictionaries / array of objects with original SQL column names. Not native Pandas, a SQL engine, Mox, or a qualified Gamma adapter.
Specification: https://leetcode.com/problems/find-churn-risk-customers/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3716.Find%20Churn%20Risk%20Customers/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Duration is last-event date minus first-event date, not wall-clock today. Same-day events use event_id ascending as an explicit adapter tie rule; not a recovered Gamma contract. Decimal result amounts are canonical exact strings.
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


def solve(subscription_events):
    _check_table(subscription_events, {"event_id": "int", "user_id": "int", "event_date": "date", "event_type": "str", "plan_name": "str?", "monthly_amount": "decimal"}, ("event_id",))
    groups = {}
    for row in subscription_events:
        if row["event_type"] not in ("start", "upgrade", "downgrade", "cancel"):
            raise ValueError("Unknown subscription event type.")
        if row["event_type"] != "cancel" and row["plan_name"] is None:
            raise ValueError("Active event needs a plan name.")
        coefficient, scale = _decimal_parts(row["monthly_amount"])
        if coefficient < 0:
            raise ValueError("Subscription amount cannot be negative.")
        groups.setdefault(row["user_id"], []).append((row, coefficient, scale))
    result = []
    for user, events in groups.items():
        events.sort(key=lambda item: (item[0]["event_date"], item[0]["event_id"]))
        last = events[-1][0]
        if last["event_type"] == "cancel" or not any(item[0]["event_type"] == "downgrade" for item in events):
            continue
        scale = max(item[2] for item in events)
        amounts = [coefficient * 10 ** (scale - item_scale) for _, coefficient, item_scale in events]
        maximum = max(amounts)
        current = amounts[-1]
        days = _date_day(last["event_date"]) - _date_day(events[0][0]["event_date"])
        if 2 * current < maximum and days >= 60:
            result.append({"user_id": user, "current_plan": last["plan_name"],
                "current_monthly_amount": _decimal_text(current, scale),
                "max_historical_amount": _decimal_text(maximum, scale), "days_as_subscriber": days})
    result.sort(key=lambda row: (-row["days_as_subscriber"], row["user_id"]))
    return result
