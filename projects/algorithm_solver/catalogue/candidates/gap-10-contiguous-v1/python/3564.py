"""3564. Seasonal Sales Analysis

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(sales, products).
O(sales + products + category-season groups + output log output) rational operations; O(products + groups) space.
Pools seasons across supplied years. Ties use exact revenue, then category ascending; absent seasons are omitted. Revenue is an exact terminating-decimal string without invented rounding.
Specification: https://leetcode.com/problems/seasonal-sales-analysis/description/
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

def checked_integer(value):
    if not -9007199254740991 <= value <= 9007199254740991:
        raise OverflowError("Integer result exceeds the mock JSON safe-integer domain.")
    return value

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

def solve(sales, products):
    validate_rows(sales, {'sale_id': 'int', 'product_id': 'int', 'sale_date': 'date', 'quantity': 'int', 'price': 'decimal'}, ['sale_id'])
    validate_rows(products, {'product_id': 'int', 'product_name': 'str', 'category': 'str'}, ['product_id'])
    categories = {row["product_id"]: row["category"] for row in products}
    season_by_month = ["Winter", "Winter", "Spring", "Spring", "Spring", "Summer", "Summer", "Summer", "Fall", "Fall", "Fall", "Winter"]
    groups = {}
    for sale in sales:
        if sale["product_id"] not in categories:
            continue
        season = season_by_month[int(sale["sale_date"][5:7]) - 1]
        category = categories[sale["product_id"]]
        key = (season, category)
        group = groups.setdefault(key, {"quantity": 0, "revenue": Fraction(0)})
        group["quantity"] += sale["quantity"]
        group["revenue"] += decimal(sale["price"]) * sale["quantity"]
    winners = {}
    for (season, category), group in groups.items():
        rank = (-group["quantity"], -group["revenue"], category)
        if season not in winners or rank < winners[season][0]:
            winners[season] = (rank, category, group)
    return [
        {"season": season, "category": category, "total_quantity": checked_integer(group["quantity"]),
         "total_revenue": exact_decimal_text(group["revenue"])}
        for season, (_, category, group) in sorted(winners.items())
    ]
