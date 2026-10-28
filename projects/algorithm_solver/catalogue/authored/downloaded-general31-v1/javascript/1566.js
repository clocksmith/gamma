'use strict';

// 1566. Detect Pattern of Length M Repeated K or More Times (Easy).
// Specification: https://leetcode.com/problems/detect-pattern-of-length-m-repeated-k-or-more-times/description/
function solve(arr, m, k) {
  for (let start = 0; start + m * k <= arr.length; start++) {
    let ok = true;
    for (let offset = 0; offset < m * k; offset++) {
      if (arr[start + offset] !== arr[start + (offset % m)]) { ok = false; break; }
    }
    if (ok) return true;
  }
  return false;
}
const containsPattern = solve;
class Solution { containsPattern(arr, m, k) { return solve(arr, m, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, containsPattern };
