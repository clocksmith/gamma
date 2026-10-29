"use strict";
// Hack2Hire 678876fe402dc47b67a14944 (Array Generation Service) over an INFERRED spec; qualification unknown.

function solve(arr, state, m) {
  const bucket = new Array(m).fill(0); // bucket[d]: largest value that becomes available before operation d + 1
  let last = -1;
  for (let i = 0; i < arr.length; i++) {
    if (state[i] === "1") last = i;
    if (last >= 0) {
      const d = i - last;
      if (d < m && arr[i] > bucket[d]) bucket[d] = arr[i];
    }
  }
  const result = [];
  let current = 0;
  for (let t = 0; t < m; t++) {
    if (bucket[t] > current) current = bucket[t];
    result.push(current);
  }
  return result;
}

function getMaximumArray(arr, state, m) { return solve(arr, state, m); }

module.exports = solve;
module.exports.getMaximumArray = getMaximumArray;
