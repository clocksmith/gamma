'use strict';

// 2231. Largest Number After Digit Swaps by Parity (Easy).
// Specification: https://leetcode.com/problems/largest-number-after-digit-swaps-by-parity/description/
// O(d log d) time, O(d) space; the declared integer domain is exact in Number.
function solve(num) {
  const digits = String(num).split('').map(Number);
  const even = [];
  const odd = [];
  for (const digit of digits) {
    if (digit % 2 === 0) even.push(digit);
    else odd.push(digit);
  }
  even.sort((left, right) => right - left);
  odd.sort((left, right) => right - left);
  let evenIndex = 0;
  let oddIndex = 0;
  let result = 0;
  for (const digit of digits) {
    const replacement = digit % 2 === 0 ? even[evenIndex++] : odd[oddIndex++];
    result = result * 10 + replacement;
  }
  return result;
}

const largestInteger = solve;
class Solution {
  largestInteger(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestInteger };
