'use strict';

// 1134. Armstrong Number (Easy).
// Specification: https://leetcode.com/problems/armstrong-number/description/
// O(d) digit operations, O(d) space; sum the d-th powers of decimal digits.
function solve(n) {
  const digits = String(n);
  let total = 0;
  for (const character of digits) total += (character.charCodeAt(0) - 48) ** digits.length;
  return total === n;
}

const isArmstrong = solve;
class Solution {
  isArmstrong(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isArmstrong };
