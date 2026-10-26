"""3642. Find Books with Polarized Opinions

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(books, readingSessions).
O(sessions + books + output log output) time; O(books with sessions) state.
Implements the numbered session-rating criteria, without collapsing repeated readers. The 60% test is exact and precedes rounding; display-score ties use title descending. The prose mention of different readers is not treated as an additional unlisted distinct-reader constraint; confirm against Gamma before promotion.
Specification: https://leetcode.com/problems/find-books-with-polarized-opinions/description/
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
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(books, readingSessions):
    validate_rows(books, {'book_id': 'int', 'title': 'str', 'author': 'str', 'genre': 'str', 'pages': 'int'}, ['book_id'])
    validate_rows(readingSessions, {'session_id': 'int', 'book_id': 'int', 'reader_name': 'str', 'pages_read': 'int', 'session_rating': 'int'}, ['session_id'])
    groups = {}
    for session in readingSessions:
        rating = session["session_rating"]
        if not 1 <= rating <= 5:
            raise ValueError("Rating is outside 1 through 5.")
        group = groups.setdefault(session["book_id"], {"count": 0, "extreme": 0, "low": rating, "high": rating})
        group["count"] += 1
        group["extreme"] += int(rating <= 2 or rating >= 4)
        group["low"] = min(group["low"], rating)
        group["high"] = max(group["high"], rating)
    result = []
    for book in books:
        group = groups.get(book["book_id"])
        if (group is None or group["count"] < 5 or group["low"] > 2 or group["high"] < 4
                or 5 * group["extreme"] < 3 * group["count"]):
            continue
        score = Fraction(group["extreme"], group["count"])
        row = {"book_id": book["book_id"], "title": book["title"], "author": book["author"],
               "genre": book["genre"], "pages": book["pages"], "rating_spread": group["high"] - group["low"],
               "polarization_score": rounded_text(score)}
        result.append((rounded_units(score), book["title"], -book["book_id"], row))
    result.sort(key=lambda item: item[:3], reverse=True)
    return [item[3] for item in result]
