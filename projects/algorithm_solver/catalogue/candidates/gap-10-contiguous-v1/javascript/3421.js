/**
 * 3421. Find Students Who Improved
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(scores).
 * O(exams + groups log groups) time; O(groups) space.
 * Compares earliest and latest exams per student/subject, not adjacent improvements or score extrema.
 * Specification: https://leetcode.com/problems/find-students-who-improved/description/
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

function solve(scores) {
  validateRows(scores, {"student_id": "int", "subject": "str", "score": "int", "exam_date": "date"}, ["student_id", "subject", "exam_date"]);
  const groups = new Map();
  for (const row of scores) {
    const key = JSON.stringify([row.student_id, row.subject]);
    if (!groups.has(key)) groups.set(key, { first: row, latest: row, count: 0 });
    const group = groups.get(key);
    group.count += 1;
    if (row.exam_date < group.first.exam_date) group.first = row;
    if (row.exam_date > group.latest.exam_date) group.latest = row;
  }
  const result = [];
  for (const group of groups.values()) {
    if (group.count >= 2 && group.latest.score > group.first.score) {
      result.push({ student_id: group.first.student_id, subject: group.first.subject,
        first_score: group.first.score, latest_score: group.latest.score });
    }
  }
  return result.sort((a, b) => a.student_id - b.student_id || compareText(a.subject, b.subject));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
