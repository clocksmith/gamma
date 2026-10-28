'use strict';

// 1394. Find Lucky Integer in an Array (Easy).
// Specification: https://leetcode.com/problems/find-lucky-integer-in-an-array/description/
function solve(arr) {
  const counts = new Map();
  for (const value of arr) counts.set(value, (counts.get(value) || 0) + 1);
  let best = -1;
  for (const [value, count] of counts.entries()) {
    if (value === count) best = Math.max(best, value);
  }
  return best;
}
const findLucky = solve;
class Solution { findLucky(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLucky };
