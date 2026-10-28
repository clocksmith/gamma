'use strict';

// 898. Bitwise ORs of Subarrays (Medium).
// Specification: https://leetcode.com/problems/bitwise-ors-of-subarrays/description/
function solve(arr) {
  const result = new Set();
  let current = new Set();
  for (const value of arr) {
    const next = new Set([value]);
    for (const v of current) next.add(v | value);
    current = next;
    for (const v of current) result.add(v);
  }
  return result.size;
}
const subarrayBitwiseORs = solve;
class Solution { subarrayBitwiseORs(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarrayBitwiseORs };
