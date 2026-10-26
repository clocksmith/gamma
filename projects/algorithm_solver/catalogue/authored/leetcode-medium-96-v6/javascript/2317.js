'use strict';

// 2317. Maximum XOR After Operations: keep each available bit in exactly one final operand.
// O(n) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only.
function solve(nums) {
  let answer = 0;
  for (const value of nums) answer |= value;
  return answer;
}

const maximumXOR = solve;
class Solution {
  maximumXOR(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumXOR };
