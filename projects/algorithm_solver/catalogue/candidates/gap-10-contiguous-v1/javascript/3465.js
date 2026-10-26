/**
 * 3465. Find Products with Valid Serial Numbers
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(products).
 * O(total description length + n log n) time; O(n) output space.
 * Case-sensitive SN. Exactly four digits on either side of the hyphen; a fifth trailing digit invalidates that occurrence. No additional word-boundary restriction is invented.
 * Specification: https://leetcode.com/problems/find-products-with-valid-serial-numbers/description/
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

function solve(products) {
  validateRows(products, {"product_id": "int", "product_name": "str", "description": "str"}, ["product_id"]);
  return products.filter(row => /SN[0-9]{4}-[0-9]{4}(?![0-9])/.test(row.description))
    .map(row => ({ product_id: row.product_id, product_name: row.product_name, description: row.description }))
    .sort((a, b) => a.product_id - b.product_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
