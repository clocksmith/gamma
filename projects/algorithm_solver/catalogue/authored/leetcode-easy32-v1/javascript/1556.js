'use strict';

// 1556. Thousand Separator (Easy).
// Specification: https://leetcode.com/problems/thousand-separator/description/
// O(d) time and space for d decimal digits. Do not depend on locale settings.
function solve(n) {
  const digits = String(n);
  const groups = [];
  for (let end = digits.length; end > 0; end -= 3) {
    groups.push(digits.slice(Math.max(0, end - 3), end));
  }
  groups.reverse();
  return groups.join('.');
}

const thousandSeparator = solve;
class Solution {
  thousandSeparator(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, thousandSeparator };
