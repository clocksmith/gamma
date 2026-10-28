'use strict';

// 357. Count Numbers with Unique Digits (Medium).
// Specification: https://leetcode.com/problems/count-numbers-with-unique-digits/description/
function solve(n) {
  if (n === 0) return 1;
  let total = 10;
  let unique = 9;
  let available = 9;
  for (let digits = 2; digits <= n; digits++) { unique *= available; available--; total += unique; }
  return total;
}
const countNumbersWithUniqueDigits = solve;
class Solution { countNumbersWithUniqueDigits(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countNumbersWithUniqueDigits };
