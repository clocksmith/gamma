'use strict';

// 3271. Hash Divided String (Medium).
// Specification: https://leetcode.com/problems/hash-divided-string/description/
function solve(s, k) {
  let out = '';
  for (let start = 0; start < s.length; start += k) {
    let sum = 0;
    for (let i = start; i < start + k; i++) sum += s.charCodeAt(i) - 97;
    out += String.fromCharCode(97 + (sum % 26));
  }
  return out;
}
const stringHash = solve;
class Solution { stringHash(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stringHash };
