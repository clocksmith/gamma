/**
 * 3586. Find COVID Recovery Patients
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(patients, covidTests).
 * O(tests + patients + output log output) time; O(patients with test results) space.
 * Finds the first negative strictly after the first positive, not the overall first negative. Calendar-day arithmetic is timezone-independent. This is a database exercise, not medical guidance.
 * Specification: https://leetcode.com/problems/find-covid-recovery-patients/description/
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

function solve(patients, covidTests) {
  validateRows(patients, {"patient_id": "int", "patient_name": "str", "age": "int"}, ["patient_id"]);
  validateRows(covidTests, {"test_id": "int", "patient_id": "int", "test_date": "date", "result": "str"}, ["test_id"]);
  const firstPositive = new Map();
  for (const row of covidTests) {
    if (!['Positive', 'Negative', 'Inconclusive'].includes(row.result)) throw new RangeError('Unknown COVID-test result.');
    if (row.result === 'Positive' && (!firstPositive.has(row.patient_id) || row.test_date < firstPositive.get(row.patient_id))) {
      firstPositive.set(row.patient_id, row.test_date);
    }
  }
  const firstNegative = new Map();
  for (const row of covidTests) {
    if (row.result === 'Negative' && firstPositive.has(row.patient_id) && row.test_date > firstPositive.get(row.patient_id) &&
        (!firstNegative.has(row.patient_id) || row.test_date < firstNegative.get(row.patient_id))) {
      firstNegative.set(row.patient_id, row.test_date);
    }
  }
  return patients.filter(row => firstNegative.has(row.patient_id))
    .map(row => ({ patient_id: row.patient_id, patient_name: row.patient_name, age: row.age,
      recovery_time: dayIndex(firstNegative.get(row.patient_id)) - dayIndex(firstPositive.get(row.patient_id)) }))
    .sort((a, b) => a.recovery_time - b.recovery_time || compareText(a.patient_name, b.patient_name) || a.patient_id - b.patient_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
