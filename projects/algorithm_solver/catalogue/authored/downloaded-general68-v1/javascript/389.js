'use strict';

// 389. Find the Difference (Easy).
// Specification: https://leetcode.com/problems/find-the-difference/description/
function solve(s, t) {
  let xor = 0;
  for (const ch of s) xor ^= ch.charCodeAt(0);
  for (const ch of t) xor ^= ch.charCodeAt(0);
  return String.fromCharCode(xor);
}
const findTheDifference = solve;
class Solution { findTheDifference(s, t) { return solve(s, t); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheDifference };
