'use strict';

// 868. Binary Gap (Easy).
// Specification: https://leetcode.com/problems/binary-gap/description/
// O(log n) time, O(1) space; measure the distance between consecutive set-bit positions.
function solve(n) {
  let remaining = n;
  let position = 0;
  let previous = -1;
  let largest = 0;
  while (remaining > 0) {
    if (remaining % 2 === 1) {
      if (previous >= 0) largest = Math.max(largest, position - previous);
      previous = position;
    }
    remaining = Math.floor(remaining / 2);
    position++;
  }
  return largest;
}

const binaryGap = solve;
class Solution {
  binaryGap(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, binaryGap };
