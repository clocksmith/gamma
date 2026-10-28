'use strict';

// 1433. Check If a String Can Break Another String (Medium).
// Specification: https://leetcode.com/problems/check-if-a-string-can-break-another-string/description/
function solve(s1, s2) {
  const a = s1.split("").sort().join("");
  const b = s2.split("").sort().join("");
  let aBreaks = true; let bBreaks = true;
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) aBreaks = false;
    if (b[i] < a[i]) bBreaks = false;
  }
  return aBreaks || bBreaks;
}
const checkIfCanBreak = solve;
class Solution { checkIfCanBreak(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkIfCanBreak };
