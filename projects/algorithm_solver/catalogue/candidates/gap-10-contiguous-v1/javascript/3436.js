/**
 * 3436. Find Valid Emails
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(users).
 * O(total text length + n log n) time; O(n) output space.
 * Nonempty ASCII local part and alphabetic domain; exactly one @; literal lowercase .com suffix; full-string matching rejects terminal newline tricks.
 * Specification: https://leetcode.com/problems/find-valid-emails/description/
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
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(users) {
  validateRows(users, {"user_id": "int", "email": "str"}, ["user_id"]);
  const pattern = /^[A-Za-z0-9_]+@[A-Za-z]+\.com$/;
  return users.filter(row => {
    const match = pattern.exec(row.email);
    return match !== null && match[0] === row.email;
  }).map(row => ({ user_id: row.user_id, email: row.email }))
    .sort((a, b) => a.user_id - b.user_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
