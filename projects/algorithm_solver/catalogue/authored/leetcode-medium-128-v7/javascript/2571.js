'use strict';

// 2571. Minimum Operations to Reduce an Integer to 0: collapse runs of set bits using signed powers of two.
// O(log(n + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n) {
  let value = n;
  let operations = 0;
  while (value > 0) {
    if ((value & 1) !== 0) {
      operations += 1;
      value += (value & 3) === 3 ? 1 : -1;
    } else value = Math.floor(value / 2);
  }
  return operations;
}

const minOperations = solve;
class Solution {
  minOperations(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
