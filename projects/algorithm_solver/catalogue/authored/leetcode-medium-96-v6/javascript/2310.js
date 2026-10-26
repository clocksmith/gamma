'use strict';

// 2310. Sum of Numbers With Units Digit K: find the first feasible count among one complete cycle of final digits.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(num, k) {
  if (num === 0) return 0;
  for (let count = 1; count <= 10; count += 1) {
    if (count * k <= num && (num - count * k) % 10 === 0) return count;
  }
  return -1;
}

const minimumNumbers = solve;
class Solution {
  minimumNumbers(num, k) { return solve(num, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumNumbers };
