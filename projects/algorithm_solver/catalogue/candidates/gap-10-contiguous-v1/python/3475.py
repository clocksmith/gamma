"""3475. DNA Pattern Recognition

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(samples).
O(total sequence length + n log n) time; O(n) output space.
All samples are returned with independent integer indicator columns; GGGG also contains a run of at least three Gs.
Specification: https://leetcode.com/problems/dna-pattern-recognition/description/
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

def solve(samples):
    validate_rows(samples, {'sample_id': 'int', 'dna_sequence': 'str', 'species': 'str'}, ['sample_id'])
    return sorted([
        {"sample_id": row["sample_id"], "dna_sequence": row["dna_sequence"], "species": row["species"],
         "has_start": int(row["dna_sequence"].startswith("ATG")),
         "has_stop": int(row["dna_sequence"].endswith(("TAA", "TAG", "TGA"))),
         "has_atat": int("ATAT" in row["dna_sequence"]), "has_ggg": int("GGG" in row["dna_sequence"])}
        for row in samples
    ], key=lambda row: row["sample_id"])
