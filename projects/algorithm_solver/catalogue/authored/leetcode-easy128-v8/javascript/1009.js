'use strict';

// 1009. Complement of Base 10 Integer (Easy).
// Specification: https://leetcode.com/problems/complement-of-base-10-integer/description/
// O(log(n + 1)) time, O(1) space; subtract from a mask with the same binary width.
function solve(n) {
  if (n === 0) return 1;
  let power = 1;
  while (power <= n) power *= 2;
  return power - 1 - n;
}

const bitwiseComplement = solve;
class Solution {
  bitwiseComplement(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bitwiseComplement };
