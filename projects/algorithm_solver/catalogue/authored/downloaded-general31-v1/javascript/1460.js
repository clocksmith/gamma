'use strict';

// 1460. Make Two Arrays Equal by Reversing Subarrays (Easy).
// Specification: https://leetcode.com/problems/make-two-arrays-equal-by-reversing-subarrays/description/
function solve(target, arr) {
  const a = target.slice().sort((x, y) => x - y);
  const b = arr.slice().sort((x, y) => x - y);
  return a.length === b.length && a.every((v, i) => v === b[i]);
}
const canBeEqual = solve;
class Solution { canBeEqual(target, arr) { return solve(target, arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canBeEqual };
