"""3626. Find Stores with Inventory Imbalance

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(stores, inventory).
O(inventory + stores + output log output) rational operations; O(inventory) space.
Counts distinct product names. Equal extreme prices use product_name then inventory_id ascending as an explicit mock tie rule. Zero expensive-product stock yields a null ratio (undefined division), ordered last. Otherwise sorts on rounded displayed ratio.
Specification: https://leetcode.com/problems/find-stores-with-inventory-imbalance/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3626.Find%20Stores%20with%20Inventory%20Imbalance/README_EN.md
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

def solve(stores, inventory):
    validate_rows(stores, {'store_id': 'int', 'store_name': 'str', 'location': 'str'}, ['store_id'])
    validate_rows(inventory, {'inventory_id': 'int', 'store_id': 'int', 'product_name': 'str', 'quantity': 'int', 'price': 'decimal'}, ['inventory_id'])
    groups = {}
    for row in inventory:
        if row["quantity"] < 0:
            raise ValueError("Inventory quantities must be nonnegative.")
        item = (decimal(row["price"]), row["product_name"], row["inventory_id"], row)
        group = groups.setdefault(row["store_id"], {"products": set(), "cheapest": item, "expensive": item})
        group["products"].add(row["product_name"])
        if item[:3] < group["cheapest"][:3]:
            group["cheapest"] = item
        current = group["expensive"]
        if (-item[0], item[1], item[2]) < (-current[0], current[1], current[2]):
            group["expensive"] = item
    result = []
    for store in stores:
        group = groups.get(store["store_id"])
        if group is None or len(group["products"]) < 3:
            continue
        cheap = group["cheapest"][3]
        expensive = group["expensive"][3]
        if expensive["quantity"] >= cheap["quantity"]:
            continue
        ratio = None if expensive["quantity"] == 0 else Fraction(cheap["quantity"], expensive["quantity"])
        units = None if ratio is None else rounded_units(ratio)
        row = {"store_id": store["store_id"], "store_name": store["store_name"], "location": store["location"],
               "most_exp_product": expensive["product_name"], "cheapest_product": cheap["product_name"],
               "imbalance_ratio": None if ratio is None else rounded_text(ratio)}
        result.append((units is None, -units if units is not None else 0, store["store_name"], store["store_id"], row))
    result.sort(key=lambda item: item[:4])
    return [item[4] for item in result]
