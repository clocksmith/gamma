"use strict";
// Hack2Hire 6a974f580ca9cc4e1c789f3b (Longest Subarray Under Limit) over an INFERRED spec; qualification unknown.

function solve(a, k) {
  let best = 0, left = 0, total = 0;
  for (let right = 0; right < a.length; right++) {
    total += a[right];
    while (total > k) total -= a[left++];
    if (right - left + 1 > best) best = right - left + 1;
  }
  return best;
}

function longestSubarrayUnderLimit(a, k) { return solve(a, k); }

module.exports = solve;
module.exports.longestSubarrayUnderLimit = longestSubarrayUnderLimit;
