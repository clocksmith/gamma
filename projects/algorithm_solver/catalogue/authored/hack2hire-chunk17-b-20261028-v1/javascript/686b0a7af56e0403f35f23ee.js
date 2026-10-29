"use strict";
// Hack2Hire 686b0a7af56e0403f35f23ee (Unequal Elements) over an INFERRED spec; qualification unknown.

function solve(elements, k) {
  const best = new Map();
  const top = new Array(k + 1).fill(0);
  for (const x of elements) {
    let row = best.get(x);
    if (row === undefined) { row = new Array(k + 1).fill(0); best.set(x, row); }
    for (let j = k; j >= 0; j--) {
      let value = row[j] + 1;
      if (j > 0 && top[j - 1] + 1 > value) value = top[j - 1] + 1;
      row[j] = value;
      if (value > top[j]) top[j] = value;
    }
  }
  return Math.max(...top);
}

function maximumLength(elements, k) { return solve(elements, k); }

module.exports = solve;
module.exports.maximumLength = maximumLength;
