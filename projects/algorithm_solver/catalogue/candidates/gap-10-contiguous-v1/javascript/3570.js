/**
 * 3570. Find Books with No Available Copies
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(libraryBooks, borrowingRecords).
 * O(books + borrowing rows + output log output) time; O(distinct borrowed books) space.
 * Only literal null/None marks an outstanding borrowing. Counts records, not unique borrower names. Zero total copies with no borrowing is excluded; negative availability is not zero availability.
 * Specification: https://leetcode.com/problems/find-books-with-no-available-copies/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3500-3599/3570.Find%20Books%20with%20No%20Available%20Copies/README_EN.md
 */

function compareText(left, right) {
  const a = Array.from(left);
  const b = Array.from(right);
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
    const difference = a[index].codePointAt(0) - b[index].codePointAt(0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  return a.length - b.length;
}

function dayIndex(value) {
  if (typeof value !== 'string' || value.length !== 10 ||
      !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value) || value.slice(0, 4) === '0000') {
    throw new TypeError('Expected a Gregorian YYYY-MM-DD date.');
  }
  const milliseconds = Date.parse(value + 'T00:00:00.000Z');
  if (!Number.isFinite(milliseconds) || new Date(milliseconds).toISOString().slice(0, 10) !== value) {
    throw new RangeError('Invalid Gregorian date.');
  }
  return milliseconds / 86400000;
}

function validateRows(rows, schema, primaryKey) {
  if (!Array.isArray(rows)) throw new TypeError('Expected a table as an array of row objects.');
  const seen = new Set();
  for (const row of rows) {
    if (row === null || typeof row !== 'object' || Array.isArray(row)) {
      throw new TypeError('Expected a row object.');
    }
    for (const [column, declared] of Object.entries(schema)) {
      if (!Object.prototype.hasOwnProperty.call(row, column)) throw new TypeError('Missing column: ' + column);
      const value = row[column];
      if (value === null && declared.endsWith('?')) continue;
      const kind = declared.replace(/\?$/, '');
      let valid = false;
      if (kind === 'int') valid = Number.isSafeInteger(value);
      else if (kind === 'str') valid = typeof value === 'string' && !Array.from(value).some(c => { const p = c.codePointAt(0); return p >= 0xD800 && p <= 0xDFFF; });
      else if (kind === 'date') { dayIndex(value); valid = true; }
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(libraryBooks, borrowingRecords) {
  validateRows(libraryBooks, {"book_id": "int", "title": "str", "author": "str", "genre": "str", "publication_year": "int", "total_copies": "int"}, ["book_id"]);
  validateRows(borrowingRecords, {"record_id": "int", "book_id": "int", "borrower_name": "str", "borrow_date": "date", "return_date": "date?"}, ["record_id"]);
  const borrowed = new Map();
  for (const row of borrowingRecords) {
    if (row.return_date === null) borrowed.set(row.book_id, (borrowed.get(row.book_id) || 0) + 1);
  }
  return libraryBooks.filter(book => (borrowed.get(book.book_id) || 0) > 0 && borrowed.get(book.book_id) === book.total_copies)
    .map(book => ({ book_id: book.book_id, title: book.title, author: book.author, genre: book.genre,
      publication_year: book.publication_year, current_borrowers: borrowed.get(book.book_id) }))
    .sort((a, b) => b.current_borrowers - a.current_borrowers || compareText(a.title, b.title) || a.book_id - b.book_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
