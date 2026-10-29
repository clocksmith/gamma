"use strict";
// Hack2Hire 677c923c5cbaff553b53b070 (Subset Sum Equals K) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  const counts = new Map();
  for (const x of nums) counts.set(x, (counts.get(x) || 0) + 1);
  const values = [...counts.keys()].sort((a, b) => a - b), d = values.length;
  const mask = (1n << BigInt(k + 1)) - 1n, suffix = new Array(d + 1);
  suffix[d] = 1n;
  for (let i = d - 1; i >= 0; i--) {
    const v = BigInt(values[i]);
    let acc = suffix[i + 1], shifted = suffix[i + 1];
    for (let j = 0; j < counts.get(values[i]); j++) {
      shifted = (shifted << v) & mask;
      if (!shifted) break;
      acc |= shifted;
    }
    suffix[i] = acc;
  }
  const out = [], combo = [];
  if (!((suffix[0] >> BigInt(k)) & 1n)) return out;
  function walk(i, rest) {
    if (rest === 0) { out.push(combo.slice()); return; }
    const v = values[i], top = Math.min(counts.get(v), Math.floor(rest / v));
    for (let j = 0; j < top; j++) combo.push(v);
    for (let j = top; j >= 0; j--) {
      if ((suffix[i + 1] >> BigInt(rest - j * v)) & 1n) walk(i + 1, rest - j * v);
      if (j) combo.pop();
    }
  }
  walk(0, k);
  return out;
}

function uniqueCombinations(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.uniqueCombinations = uniqueCombinations;
