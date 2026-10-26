'use strict';

// 1780. Check if Number is a Sum of Powers of Three: reject a ternary representation containing the digit two.
// O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(n) {
  let remaining = n;
  while (remaining > 0) {
    if (remaining % 3 === 2) return false;
    remaining = Math.floor(remaining / 3);
  }
  return true;
}

const checkPowersOfThree = solve;
class Solution {
  checkPowersOfThree(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkPowersOfThree };
