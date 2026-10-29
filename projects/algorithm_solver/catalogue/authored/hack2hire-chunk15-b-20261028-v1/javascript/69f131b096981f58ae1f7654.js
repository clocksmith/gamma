"use strict";
// Hack2Hire 69f131b096981f58ae1f7654 (Find K Distinct Element Subarray) over an INFERRED spec; qualification unknown.

function solve(arr, k) {
  const counts = new Map();
  let distinct = 0, best = -1, left = 0;
  for (let right = 0; right < arr.length; right++) {
    const x = arr[right];
    const c = (counts.get(x) || 0) + 1;
    counts.set(x, c);
    if (c === 1) distinct++;
    while (distinct >= k) {
      const length = right - left + 1;
      if (best < 0 || length < best) best = length;
      const y = arr[left];
      const d = counts.get(y) - 1;
      counts.set(y, d);
      if (d === 0) distinct--;
      left++;
    }
  }
  return best;
}

function shortestGoodSubarray(arr, k) { return solve(arr, k); }

module.exports = solve;
module.exports.shortestGoodSubarray = shortestGoodSubarray;
