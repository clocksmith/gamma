'use strict';

// 1545. Find Kth Bit in Nth Binary String (Medium).
// Specification: https://leetcode.com/problems/find-kth-bit-in-nth-binary-string/description/
function solve(n, k) {
  let text = '0';
  for (let step = 1; step < n; step++) {
    const inverted = [...text].reverse().map((ch) => ch === '0' ? '1' : '0').join('');
    text = text + '1' + inverted;
  }
  return text[k - 1];
}
const findKthBit = solve;
class Solution { findKthBit(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthBit };
