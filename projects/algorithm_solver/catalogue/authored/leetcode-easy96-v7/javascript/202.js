'use strict';

// 202. Happy Number (Easy).
// Specification: https://leetcode.com/problems/happy-number/description/
// O(log n) initial digit work and bounded subsequent states for the 32-bit domain.
function solve(n) {
  const seen = new Set();
  let current = n;
  while (current !== 1 && !seen.has(current)) {
    seen.add(current);
    let next = 0;
    while (current > 0) {
      const digit = current % 10;
      next += digit * digit;
      current = Math.floor(current / 10);
    }
    current = next;
  }
  return current === 1;
}

const isHappy = solve;
class Solution {
  isHappy(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isHappy };
