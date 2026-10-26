/**
 * 3601. Find Drivers with Improved Fuel Efficiency
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(drivers, trips).
 * O(trips + drivers + output log output) rational operations; O(drivers) rational state. Exact fraction arithmetic has operand-size-dependent cost.
 * Uses the arithmetic mean of trip efficiencies, not a ratio of summed distance/fuel. Filters positive improvement before rounding; sorts by the displayed rounded improvement. Half-year groups pool all supplied dates, without inventing a year column. Undefined zero-fuel ratios are ignored.
 * Specification: https://leetcode.com/problems/find-drivers-with-improved-fuel-efficiency/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3601.Find%20Drivers%20with%20Improved%20Fuel%20Efficiency/README_EN.md
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

function solve(drivers, trips) {
  validateRows(drivers, {"driver_id": "int", "driver_name": "str"}, ["driver_id"]);
  validateRows(trips, {"trip_id": "int", "driver_id": "int", "trip_date": "date", "distance_km": "decimal", "fuel_consumed": "decimal"}, ["trip_id"]);
  const groups = new Map();
  for (const trip of trips) {
    const fuel = decimal(trip.fuel_consumed);
    // SQL division by zero produces NULL; AVG does not count that undefined ratio.
    if (fuel.n === 0n) continue;
    if (!groups.has(trip.driver_id)) groups.set(trip.driver_id, [{ sum: rational(0n), count: 0 }, { sum: rational(0n), count: 0 }]);
    const half = Number(trip.trip_date.slice(5, 7)) <= 6 ? 0 : 1;
    const group = groups.get(trip.driver_id)[half];
    group.sum = addRational(group.sum, divideRational(decimal(trip.distance_km), fuel));
    group.count += 1;
  }
  const result = [];
  for (const driver of drivers) {
    const halves = groups.get(driver.driver_id);
    if (!halves || halves[0].count === 0 || halves[1].count === 0) continue;
    const first = divideRational(halves[0].sum, rational(BigInt(halves[0].count)));
    const second = divideRational(halves[1].sum, rational(BigInt(halves[1].count)));
    const improvement = subtractRational(second, first);
    if (improvement.n <= 0n) continue;
    result.push({ units: roundedUnits(improvement), row: {
      driver_id: driver.driver_id, driver_name: driver.driver_name,
      first_half_avg: roundedText(first), second_half_avg: roundedText(second),
      efficiency_improvement: roundedText(improvement),
    } });
  }
  result.sort((a, b) => a.units !== b.units ? (a.units > b.units ? -1 : 1) :
    compareText(a.row.driver_name, b.row.driver_name) || a.row.driver_id - b.row.driver_id);
  return result.map(item => item.row);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
