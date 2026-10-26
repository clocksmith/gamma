'use strict';

// 1356. Sort Integers by The Number of 1 Bits (Easy).
// Specification: https://leetcode.com/problems/sort-integers-by-the-number-of-1-bits/description/
// O(n * b + n log n) time, O(n) space; b <= 14 in the declared domain.
function solve(arr) {
  const ranked = [];
  for (const value of arr) {
    let remaining = value;
    let bits = 0;
    while (remaining > 0) {
      remaining &= remaining - 1;
      bits++;
    }
    ranked.push([bits, value]);
  }
  ranked.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  return ranked.map(entry => entry[1]);
}

const sortByBits = solve;
class Solution {
  sortByBits(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortByBits };
