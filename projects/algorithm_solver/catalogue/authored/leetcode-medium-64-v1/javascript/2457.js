'use strict';

// 2457. Minimum Addition to Make Integer Beautiful: round upward at successive decimal places until the digit sum fits.
// O(d^2) time and O(1) auxiliary space for at most 13 decimal digits; inputs are read-only.
function solve(n, target) {
  function digitSum(value) {
    let total = 0;
    while (value > 0) {
      total += value % 10;
      value = Math.floor(value / 10);
    }
    return total;
  }
  let current = n;
  let place = 10;
  while (digitSum(current) > target) {
    current = Math.floor((current + place - 1) / place) * place;
    place *= 10;
  }
  return current - n;
}

const makeIntegerBeautiful = solve;
class Solution {
  makeIntegerBeautiful(n, target) { return solve(n, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeIntegerBeautiful };
