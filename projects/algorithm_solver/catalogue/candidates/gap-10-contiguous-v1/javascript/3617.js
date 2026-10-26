/**
 * 3617. Find Students with Study Spiral Pattern
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(students, studySessions).
 * O(sessions log sessions + students + output log output) rational operations; O(sessions) space.
 * Explicit interpretation from the pinned reference: the entire ordered student history must be complete repetitions of its distinct-subject cycle, with no gap over two days. No search for a qualifying subwindow; incomplete final cycles reject. Same-date sessions use session_id ascending. These choices require Gamma contract approval.
 * Specification: https://leetcode.com/problems/find-students-with-study-spiral-pattern/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3617.Find%20Students%20with%20Study%20Spiral%20Pattern/README_EN.md
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

function rational(numerator, denominator = 1n) {
  if (denominator === 0n) throw new RangeError('Zero rational denominator.');
  if (denominator < 0n) {
    numerator = -numerator;
    denominator = -denominator;
  }
  let a = numerator < 0n ? -numerator : numerator;
  let b = denominator;
  while (b !== 0n) [a, b] = [b, a % b];
  return { n: numerator / a, d: denominator / a };
}

function decimal(value) {
  if ((typeof value !== 'string' && typeof value !== 'number') ||
      (typeof value === 'number' && !Number.isFinite(value))) {
    throw new TypeError('Expected a finite decimal number or decimal string.');
  }
  const text = String(value);
  const match = /^([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(text);
  if (!match || match[0] !== text || text.length > 1024) {
    throw new TypeError('Invalid mock decimal representation.');
  }
  const fraction = match[3] || '';
  const exponent = Number(match[4] || 0) - fraction.length;
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) {
    throw new RangeError('Mock decimal exponent exceeds the declared bound.');
  }
  let numerator = BigInt(match[2] + fraction);
  if (match[1] === '-') numerator = -numerator;
  return exponent >= 0
    ? rational(numerator * (10n ** BigInt(exponent)))
    : rational(numerator, 10n ** BigInt(-exponent));
}

function addRational(a, b) {
  return rational(a.n * b.d + b.n * a.d, a.d * b.d);
}

function subtractRational(a, b) {
  return rational(a.n * b.d - b.n * a.d, a.d * b.d);
}

function divideRational(a, b) {
  return rational(a.n * b.d, a.d * b.n);
}

function compareRational(a, b) {
  const difference = a.n * b.d - b.n * a.d;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function roundedUnits(value, places = 2) {
  const magnitude = (value.n < 0n ? -value.n : value.n) * (10n ** BigInt(places));
  let quotient = magnitude / value.d;
  if (2n * (magnitude % value.d) >= value.d) quotient += 1n;
  return value.n < 0n ? -quotient : quotient;
}

function unitsText(units, places, trim = false) {
  const sign = units < 0n ? '-' : '';
  let digits = (units < 0n ? -units : units).toString();
  if (places === 0) return sign + digits;
  digits = digits.padStart(places + 1, '0');
  let text = sign + digits.slice(0, -places) + '.' + digits.slice(-places);
  if (trim) text = text.replace(/0+$/, '').replace(/\.$/, '');
  return text;
}

function roundedText(value, places = 2) {
  return unitsText(roundedUnits(value, places), places);
}

function exactDecimalText(value) {
  let denominator = value.d;
  let twos = 0;
  let fives = 0;
  while (denominator % 2n === 0n) { denominator /= 2n; twos += 1; }
  while (denominator % 5n === 0n) { denominator /= 5n; fives += 1; }
  if (denominator !== 1n) throw new RangeError('Nonterminating decimal requires an explicit rounding rule.');
  const places = Math.max(twos, fives);
  const units = value.n * (10n ** BigInt(places)) / value.d;
  return unitsText(units, places, true);
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
      else if (kind === 'decimal') { decimal(value); valid = true; }
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(students, studySessions) {
  validateRows(students, {"student_id": "int", "student_name": "str", "major": "str"}, ["student_id"]);
  validateRows(studySessions, {"session_id": "int", "student_id": "int", "subject": "str", "session_date": "date", "hours_studied": "decimal"}, ["session_id"]);
  const groups = new Map();
  for (const session of studySessions) {
    if (!groups.has(session.student_id)) groups.set(session.student_id, []);
    groups.get(session.student_id).push(session);
  }
  const result = [];
  for (const student of students) {
    const sessions = groups.get(student.student_id) || [];
    sessions.sort((a, b) => compareText(a.session_date, b.session_date) || a.session_id - b.session_id);
    const cycleLength = new Set(sessions.map(row => row.subject)).size;
    if (cycleLength < 3 || sessions.length < 2 * cycleLength || sessions.length % cycleLength !== 0) continue;
    let valid = true;
    let hours = rational(0n);
    for (let index = 0; index < sessions.length; index += 1) {
      if (sessions[index].subject !== sessions[index % cycleLength].subject ||
          (index > 0 && dayIndex(sessions[index].session_date) - dayIndex(sessions[index - 1].session_date) > 2)) {
        valid = false;
        break;
      }
      hours = addRational(hours, decimal(sessions[index].hours_studied));
    }
    if (valid) result.push({ hours, row: { student_id: student.student_id, student_name: student.student_name,
      major: student.major, cycle_length: cycleLength, total_study_hours: exactDecimalText(hours) } });
  }
  result.sort((a, b) => b.row.cycle_length - a.row.cycle_length || compareRational(b.hours, a.hours) || a.row.student_id - b.row.student_id);
  return result.map(item => item.row);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
