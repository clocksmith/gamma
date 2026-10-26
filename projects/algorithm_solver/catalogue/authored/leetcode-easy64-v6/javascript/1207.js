'use strict';

// 1207. Unique Number of Occurrences (Easy).
// Specification: https://leetcode.com/problems/unique-number-of-occurrences/description/
// O(n) expected time, O(n) space; preserve arr.
function solve(arr) {
  const counts = new Map();
  for (const value of arr) counts.set(value, (counts.get(value) || 0) + 1);
  const frequencies = new Set();
  for (const count of counts.values()) {
    if (frequencies.has(count)) return false;
    frequencies.add(count);
  }
  return true;
}

const uniqueOccurrences = solve;
class Solution {
  uniqueOccurrences(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, uniqueOccurrences };
