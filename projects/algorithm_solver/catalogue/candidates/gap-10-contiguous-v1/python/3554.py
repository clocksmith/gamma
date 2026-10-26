"""3554. Find Category Recommendation Pairs

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(productPurchases, productInfo).
O(purchases + products + sum(categories_user^2) + output log output) time; O(purchases + distinct pairs) space.
Deduplicates categories per user before forming pairs, so purchases of several products in one category never inflate counts. Category collation is Unicode scalar order in both languages.
Specification: https://leetcode.com/problems/find-category-recommendation-pairs/description/
"""

import re
import math
from fractions import Fraction

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
            elif kind == "decimal":
                decimal(value)
                valid = True
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(productPurchases, productInfo):
    validate_rows(productPurchases, {'user_id': 'int', 'product_id': 'int', 'quantity': 'int'}, ['user_id', 'product_id'])
    validate_rows(productInfo, {'product_id': 'int', 'category': 'str', 'price': 'decimal'}, ['product_id'])
    info = {row["product_id"]: row["category"] for row in productInfo}
    by_user = {}
    for row in productPurchases:
        if row["product_id"] in info:
            by_user.setdefault(row["user_id"], set()).add(info[row["product_id"]])
    pairs = {}
    for purchased in by_user.values():
        categories = sorted(purchased)
        for left in range(len(categories)):
            for right in range(left + 1, len(categories)):
                pair = (categories[left], categories[right])
                pairs[pair] = pairs.get(pair, 0) + 1
    result = [{"category1": a, "category2": b, "customer_count": count}
              for (a, b), count in pairs.items() if count >= 3]
    return sorted(result, key=lambda row: (-row["customer_count"], row["category1"], row["category2"]))
