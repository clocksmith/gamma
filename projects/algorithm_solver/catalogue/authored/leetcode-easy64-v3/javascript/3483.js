'use strict';

// 3483. Unique 3-Digit Even Numbers (Easy).
// Specification: https://leetcode.com/problems/unique-3-digit-even-numbers/description/
// O(n + 450) time, O(1) space; enumerate digit values with multiplicities, not indices.
function solve(digits) {
  const counts = new Array(10).fill(0);
  for (const digit of digits) counts[digit]++;
  let result = 0;
  for (let hundreds = 1; hundreds <= 9; hundreds++) {
    if (counts[hundreds] === 0) continue;
    counts[hundreds]--;
    for (let tens = 0; tens <= 9; tens++) {
      if (counts[tens] === 0) continue;
      counts[tens]--;
      for (let units = 0; units <= 8; units += 2) {
        if (counts[units] > 0) result++;
      }
      counts[tens]++;
    }
    counts[hundreds]++;
  }
  return result;
}

const totalNumbers = solve;
class Solution {
  totalNumbers(digits) { return solve(digits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalNumbers };
