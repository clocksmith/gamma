'use strict';

// 1362. Closest Divisors: find the closest factor pair for each of the two permitted products.
// O(sqrt(num + 2)) time and O(1) auxiliary space; inputs are read-only.
function solve(num) {
  function factors(value) {
    let divisor = Math.floor(Math.sqrt(value));
    while (value % divisor !== 0) divisor -= 1;
    return [divisor, value / divisor];
  }
  const first = factors(num + 1);
  const second = factors(num + 2);
  return first[1] - first[0] <= second[1] - second[0] ? first : second;
}

const closestDivisors = solve;
class Solution {
  closestDivisors(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestDivisors };
