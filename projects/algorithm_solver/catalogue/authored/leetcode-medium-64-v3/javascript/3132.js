'use strict';

// 3132. Find the Integer Added to Array II: try the three possible retained minima and verify sorted subsequence matches.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  const first = [...nums1].sort((left, right) => left - right);
  const second = [...nums2].sort((left, right) => left - right);
  let best = Infinity;
  for (let start = 0; start < 3; start += 1) {
    const difference = second[0] - first[start];
    let matched = 0;
    let removed = 0;
    for (const value of first) {
      if (matched < second.length && value + difference === second[matched]) matched += 1;
      else {
        removed += 1;
        if (removed > 2) break;
      }
    }
    if (matched === second.length && removed === 2) best = Math.min(best, difference);
  }
  return best;
}

const minimumAddedInteger = solve;
class Solution {
  minimumAddedInteger(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumAddedInteger };
