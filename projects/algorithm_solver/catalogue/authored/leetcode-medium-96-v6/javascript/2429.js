'use strict';

// 2429. Minimize XOR: match the highest valuable set bits first and place remaining bits at the bottom.
// O(31) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only.
function solve(num1, num2) {
  let bits = num2;
  let remaining = 0;
  while (bits) {
    bits &= bits - 1;
    remaining += 1;
  }
  let answer = 0;
  for (let bit = 30; bit >= 0; bit -= 1) {
    const mask = 1 << bit;
    if (remaining > 0 && (num1 & mask) !== 0) {
      answer |= mask;
      remaining -= 1;
    }
  }
  for (let bit = 0; bit < 31; bit += 1) {
    const mask = 1 << bit;
    if (remaining > 0 && (answer & mask) === 0) {
      answer |= mask;
      remaining -= 1;
    }
  }
  return answer;
}

const minimizeXor = solve;
class Solution {
  minimizeXor(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeXor };
