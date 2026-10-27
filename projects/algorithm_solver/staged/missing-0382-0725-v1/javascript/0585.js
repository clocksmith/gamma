'use strict';

// 585. Investments in 2016. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. insurance: pid, tiv_2015, tiv_2016, lat, lon. Output: tiv_2016. Decimal summation rounds once; SUM over no qualifying rows is NULL.

function _roundedRatio(numerator, denominator, places) {
  let a = BigInt(numerator);
  let b = BigInt(denominator);
  const sign = (a < 0n) !== (b < 0n) ? -1 : 1;
  if (a < 0n) a = -a;
  if (b < 0n) b = -b;
  const scale = 10n ** BigInt(places);
  const rounded = (2n * a * scale + b) / (2n * b);
  return sign * Number(rounded) / Number(scale);
}

function _decimalParts(value) {
  const [mantissa, exponentText = '0'] = String(value).toLowerCase().split('e');
  const negative = mantissa.startsWith('-');
  const unsigned = mantissa.replace(/^[+-]/, '');
  const [whole, fraction = ''] = unsigned.split('.');
  let coefficient = BigInt((whole || '0') + fraction);
  let scale = fraction.length - Number(exponentText);
  if (scale < 0) { coefficient *= 10n ** BigInt(-scale); scale = 0; }
  return [negative ? -coefficient : coefficient, scale];
}
function _sumRounded(values) {
  if (values.length === 0) return null;
  const parts = values.map(_decimalParts);
  let scale = 0;
  for (const part of parts) scale = Math.max(scale, part[1]);
  let total = 0n;
  for (const [value, digits] of parts) total += value * 10n ** BigInt(scale - digits);
  return _roundedRatio(total, 10n ** BigInt(scale), 2);
}

function solve(insurance) {
  const values = new Map();
  const positions = new Map();
  for (const row of insurance) {
    const key = JSON.stringify([row.lat, row.lon]);
    values.set(row.tiv_2015, (values.get(row.tiv_2015) || 0) + 1);
    positions.set(key, (positions.get(key) || 0) + 1);
  }
  const selected = insurance.filter(row => values.get(row.tiv_2015) > 1 && positions.get(JSON.stringify([row.lat, row.lon])) === 1);
  return [{tiv_2016: _sumRounded(selected.map(row => row.tiv_2016))}];
}

const investments = solve;
class Solution {
  investments(insurance) { return solve(insurance); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, investments };
