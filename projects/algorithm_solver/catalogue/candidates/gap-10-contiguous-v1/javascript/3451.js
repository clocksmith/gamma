/**
 * 3451. Find Invalid IP Addresses
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(logs).
 * O(total IP length + distinct invalid IPs log count) time; O(distinct invalid IPs) space.
 * Counts distinct log rows by the original IP string; valid zero octets are allowed, leading-zero multi-digit octets are not.
 * Specification: https://leetcode.com/problems/find-invalid-ip-addresses/description/
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

function solve(logs) {
  validateRows(logs, {"log_id": "int", "ip": "str", "status_code": "int"}, ["log_id"]);
  const counts = new Map();
  for (const row of logs) {
    const parts = row.ip.split('.');
    const valid = parts.length === 4 && parts.every(part => {
      const match = /^[0-9]{1,3}$/.exec(part);
      return match !== null && match[0] === part &&
        (part.length === 1 || part[0] !== '0') && Number(part) <= 255;
    });
    if (!valid) counts.set(row.ip, (counts.get(row.ip) || 0) + 1);
  }
  return [...counts].map(([ip, count]) => ({ ip, invalid_count: count }))
    .sort((a, b) => b.invalid_count - a.invalid_count || compareText(b.ip, a.ip));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
