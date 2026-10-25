'use strict';

// 1952. Three Divisors (Easy).
// Specification: https://leetcode.com/problems/three-divisors/description/
// O(n^(1/4)) time, O(1) space. Exactly three divisors means a prime square.
function solve(n) {
  const root = Math.floor(Math.sqrt(n));
  if (root < 2 || root * root !== n) return false;
  for (let divisor = 2; divisor * divisor <= root; divisor++) {
    if (root % divisor === 0) return false;
  }
  return true;
}

const isThree = solve;
class Solution {
  isThree(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isThree };
