/**
 * 3415. Find Products with Three Consecutive Digits
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(products).
 * O(total text length + n log n) time; O(total text length + n) transient space.
 * Requires an isolated maximal ASCII digit run of length three. A longer digit run is never split into triples. A separate longer run does not invalidate a qualifying triple, following the consulted regex solution.
 * Specification: https://leetcode.com/problems/find-products-with-three-consecutive-digits/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3400-3499/3415.Find%20Products%20with%20Three%20Consecutive%20Digits/README_EN.md
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
  validateRows(products, {"product_id": "int", "name": "str"}, ["product_id"]);
  return products.filter(row => (row.name.match(/[0-9]+/g) || []).some(run => run.length === 3))
    .map(row => ({ product_id: row.product_id, name: row.name }))
    .sort((a, b) => a.product_id - b.product_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
