/**
 * 3580. Find Consistently Improving Employees
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(employees, performanceReviews).
 * O(reviews log reviews + employees + output log output) time; O(reviews) space.
 * Only the most recent three reviews count. Equal review dates are ordered by review_id as a declared mock tie rule; the public wording does not independently qualify that tie rule.
 * Specification: https://leetcode.com/problems/find-consistently-improving-employees/description/
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

function solve(employees, performanceReviews) {
  validateRows(employees, {"employee_id": "int", "name": "str"}, ["employee_id"]);
  validateRows(performanceReviews, {"review_id": "int", "employee_id": "int", "review_date": "date", "rating": "int"}, ["review_id"]);
  const grouped = new Map();
  for (const row of performanceReviews) {
    if (!grouped.has(row.employee_id)) grouped.set(row.employee_id, []);
    grouped.get(row.employee_id).push(row);
  }
  const result = [];
  for (const employee of employees) {
    const reviews = grouped.get(employee.employee_id) || [];
    reviews.sort((a, b) => compareText(b.review_date, a.review_date) || b.review_id - a.review_id);
    if (reviews.length >= 3 && reviews[0].rating > reviews[1].rating && reviews[1].rating > reviews[2].rating) {
      result.push({ employee_id: employee.employee_id, name: employee.name,
        improvement_score: reviews[0].rating - reviews[2].rating });
    }
  }
  return result.sort((a, b) => b.improvement_score - a.improvement_score || compareText(a.name, b.name) || a.employee_id - b.employee_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
