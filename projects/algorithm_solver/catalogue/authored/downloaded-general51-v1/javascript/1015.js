'use strict';

// 1015. Smallest Integer Divisible by K (Medium).
// Specification: https://leetcode.com/problems/smallest-integer-divisible-by-k/description/
function solve(k) {
  if (k % 2 === 0 || k % 5 === 0) return -1;
  let remainder = 0;
  for (let length = 1; length <= k; length++) {
    remainder = (remainder * 10 + 1) % k;
    if (remainder === 0) return length;
  }
  return -1;
}
const smallestRepunitDivByK = solve;
class Solution { smallestRepunitDivByK(k) { return solve(k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestRepunitDivByK };
