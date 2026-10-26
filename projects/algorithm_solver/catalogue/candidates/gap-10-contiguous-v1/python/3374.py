"""3374. First Letter Capitalization II

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(userContent).
O(total text length + n log n) time; O(total output length) space.
Uses the currently visible English-letter/hyphen rule. Space is U+0020. Punctuation and repeated spacing are preserved; output order is deterministically content_id ascending.
Specification: https://leetcode.com/problems/first-letter-capitalization-ii/description/
"""

import re

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

def solve(userContent):
    validate_rows(userContent, {'content_id': 'int', 'content_text': 'str'}, ['content_id'])
    def title_part(part):
        return part[0].upper() + part[1:].lower()

    def convert_word(match):
        word = match.group(0)
        if re.match(r"[A-Za-z]", word) is None:
            return word
        if re.fullmatch(r"[A-Za-z]+(?:-[A-Za-z]+)+", word):
            return "-".join(title_part(part) for part in word.split("-"))
        return word[0].upper() + re.sub(r"[A-Z]", lambda part: part.group(0).lower(), word[1:])

    return sorted([
        {"content_id": row["content_id"], "original_text": row["content_text"],
         "converted_text": re.sub(r"[^ ]+", convert_word, row["content_text"])}
        for row in userContent
    ], key=lambda row: row["content_id"])
