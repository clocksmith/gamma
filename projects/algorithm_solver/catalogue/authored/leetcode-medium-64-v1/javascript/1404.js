'use strict';

// 1404. Number of Steps to Reduce a Number in Binary Representation to One: scan low bits while carrying additions instead of parsing a large integer.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let carry = 0;
  let steps = 0;
  for (let index = s.length - 1; index > 0; index -= 1) {
    const bit = s.charCodeAt(index) - 48 + carry;
    if (bit === 1) {
      steps += 2;
      carry = 1;
    } else {
      steps += 1;
    }
  }
  return steps + carry;
}

const numSteps = solve;
class Solution {
  numSteps(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSteps };
