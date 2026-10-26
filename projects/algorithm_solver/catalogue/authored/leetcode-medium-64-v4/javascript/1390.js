'use strict';

// 1390. Four Divisors: enumerate divisor pairs and stop after the fourth divisor is exceeded.
// O(n * sqrt(M)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only.
function solve(nums) {
  let total = 0;
  for (const value of nums) {
    let count = 0;
    let subtotal = 0;
    for (let divisor = 1; divisor * divisor <= value; divisor += 1) {
      if (value % divisor !== 0) continue;
      const partner = value / divisor;
      if (partner === divisor) {
        count += 1;
        subtotal += divisor;
      } else {
        count += 2;
        subtotal += divisor + partner;
      }
      if (count > 4) break;
    }
    if (count === 4) total += subtotal;
  }
  return total;
}

const sumFourDivisors = solve;
class Solution {
  sumFourDivisors(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumFourDivisors };
