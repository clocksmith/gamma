/**
 * 3374. First Letter Capitalization II
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(userContent).
 * O(total text length + n log n) time; O(total output length) space.
 * Uses the currently visible English-letter/hyphen rule. Space is U+0020. Punctuation and repeated spacing are preserved; output order is deterministically content_id ascending.
 * Specification: https://leetcode.com/problems/first-letter-capitalization-ii/description/
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

function solve(userContent) {
  validateRows(userContent, {"content_id": "int", "content_text": "str"}, ["content_id"]);
  const titlePart = part => part[0].toUpperCase() + part.slice(1).toLowerCase();
  const convertWord = word => {
    if (!/^[A-Za-z]/.test(word)) return word;
    if (/^[A-Za-z]+(?:-[A-Za-z]+)+$/.test(word)) {
      return word.split('-').map(titlePart).join('-');
    }
    return word[0].toUpperCase() + word.slice(1).replace(/[A-Z]/g, letter => letter.toLowerCase());
  };
  return userContent.map(row => ({
    content_id: row.content_id,
    original_text: row.content_text,
    converted_text: row.content_text.replace(/[^ ]+/g, convertWord),
  })).sort((a, b) => a.content_id - b.content_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
