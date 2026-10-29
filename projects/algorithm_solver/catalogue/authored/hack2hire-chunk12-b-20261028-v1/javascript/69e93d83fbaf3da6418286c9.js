"use strict";
// Hack2Hire 69e93d83fbaf3da6418286c9 (Minimum Subarray with K Unique Integers) over an INFERRED spec; qualification unknown.

function solve(arr, k) {
  const counts = new Map();
  let best = -1, left = 0;
  for (let right = 0; right < arr.length; right++) {
    counts.set(arr[right], (counts.get(arr[right]) || 0) + 1);
    while (counts.size >= k) {
      const length = right - left + 1;
      if (best === -1 || length < best) best = length;
      const w = arr[left];
      const c = counts.get(w) - 1;
      if (c === 0) counts.delete(w); else counts.set(w, c);
      left++;
    }
  }
  return best;
}

function minLengthGoodSubarray(arr, k) { return solve(arr, k); }

module.exports = solve;
module.exports.minLengthGoodSubarray = minLengthGoodSubarray;
