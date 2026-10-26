'use strict';

// 3216. Lexicographically Smallest String After a Swap (Easy).
// Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-a-swap/description/
// O(n) time and space; perform only the first improving adjacent same-parity swap.
function solve(s) {
  const digits = s.split('');
  for (let index = 0; index + 1 < digits.length; index++) {
    if (digits[index] > digits[index + 1] && (digits[index].charCodeAt(0) - digits[index + 1].charCodeAt(0)) % 2 === 0) {
      const first = digits[index];
      digits[index] = digits[index + 1];
      digits[index + 1] = first;
      break;
    }
  }
  return digits.join('');
}

const getSmallestString = solve;
class Solution {
  getSmallestString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSmallestString };
