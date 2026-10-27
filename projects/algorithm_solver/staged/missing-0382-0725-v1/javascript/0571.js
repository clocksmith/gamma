'use strict';

// 571. Find Median Given Frequency of Numbers. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. numbers: num, frequency. Output: median. Frequencies are nonnegative; no decompressed array is allocated.

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

function solve(numbers) {
  let total = 0n;
  for (const row of numbers) total += BigInt(row.frequency);
  if (total === 0n) return [{median: null}];
  const targets = [(total + 1n) / 2n, total / 2n + 1n];
  let cumulative = 0n;
  let sum = 0n;
  for (const row of numbers.slice().sort((a, b) => a.num - b.num)) {
    const previous = cumulative;
    cumulative += BigInt(row.frequency);
    for (const rank of targets) if (previous < rank && rank <= cumulative) sum += BigInt(row.num);
  }
  return [{median: _roundedRatio(sum, 2, 1)}];
}

const medianFrequency = solve;
class Solution {
  medianFrequency(numbers) { return solve(numbers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, medianFrequency };
