"use strict";
// Hack2Hire 6a7253d448af2ae18e995e99 (Minimum Nondecreasing Increment); INFERRED spec; qualification unknown.
function solve(arr) {
  const n = arr.length;
  let x = 0, previousForced = -2;
  for (let i = 0; i + 1 < n; i++) {
    if (arr[i] > arr[i + 1]) {
      if (previousForced === i) return -1;  // i and i+1 would both need to be chosen
      previousForced = i + 1;
      x = Math.max(x, arr[i] - arr[i + 1]);
    }
  }
  for (let i = 0; i + 1 < n; i++) if (arr[i] > arr[i + 1] && i + 2 < n && arr[i + 1] + x > arr[i + 2]) return -1;
  return x;
}
function minNondecreasingIncrement(arr) { return solve(arr); }
module.exports = solve;
module.exports.minNondecreasingIncrement = minNondecreasingIncrement;
