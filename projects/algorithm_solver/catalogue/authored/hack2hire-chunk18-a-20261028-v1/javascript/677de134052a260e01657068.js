"use strict";
// Hack2Hire 677de134052a260e01657068 (Make Array Bitonic) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const n = arr.length;
  const left = new Array(n);
  const right = new Array(n);
  for (let c = 0; c < n; c++) left[c] = c === 0 ? arr[c] : Math.min(arr[c], left[c - 1] + 1);
  for (let c = n - 1; c >= 0; c--) right[c] = c === n - 1 ? arr[c] : Math.min(arr[c], right[c + 1] + 1);
  let best = 0;
  let total = 0;
  for (let c = 0; c < n; c++) {
    total += arr[c];
    const k = Math.min(c + 1, n - c, left[c], right[c]);
    if (k > best) best = k;
  }
  return total - best * best;
}

function minOperationsToBitonic(arr) { return solve(arr); }

module.exports = solve;
module.exports.minOperationsToBitonic = minOperationsToBitonic;
