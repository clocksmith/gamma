"""3570. Find Books with No Available Copies

Authored candidate. Not executed, syntax-checked, tested, or qualified.
Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
Signature: solve(libraryBooks, borrowingRecords).
O(books + borrowing rows + output log output) time; O(distinct borrowed books) space.
Only literal null/None marks an outstanding borrowing. Counts records, not unique borrower names. Zero total copies with no borrowing is excluded; negative availability is not zero availability.
Specification: https://leetcode.com/problems/find-books-with-no-available-copies/description/
Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3500-3599/3570.Find%20Books%20with%20No%20Available%20Copies/README_EN.md
"""

import re
from datetime import date

def day_index(value):
    if not isinstance(value, str) or len(value) != 10 or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise TypeError("Expected a Gregorian YYYY-MM-DD date.")
    return date.fromisoformat(value).toordinal()

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
            if not valid:
                raise TypeError("Invalid value for column: " + column)
        key = tuple(row[column] for column in primary_key)
        if key in seen:
            raise ValueError("Duplicate primary key.")
        seen.add(key)

def solve(libraryBooks, borrowingRecords):
    validate_rows(libraryBooks, {'book_id': 'int', 'title': 'str', 'author': 'str', 'genre': 'str', 'publication_year': 'int', 'total_copies': 'int'}, ['book_id'])
    validate_rows(borrowingRecords, {'record_id': 'int', 'book_id': 'int', 'borrower_name': 'str', 'borrow_date': 'date', 'return_date': 'date?'}, ['record_id'])
    borrowed = {}
    for row in borrowingRecords:
        if row["return_date"] is None:
            book_id = row["book_id"]
            borrowed[book_id] = borrowed.get(book_id, 0) + 1
    result = [
        {"book_id": book["book_id"], "title": book["title"], "author": book["author"], "genre": book["genre"],
         "publication_year": book["publication_year"], "current_borrowers": borrowed[book["book_id"]]}
        for book in libraryBooks
        if borrowed.get(book["book_id"], 0) > 0 and borrowed[book["book_id"]] == book["total_copies"]
    ]
    return sorted(result, key=lambda row: (-row["current_borrowers"], row["title"], row["book_id"]))
