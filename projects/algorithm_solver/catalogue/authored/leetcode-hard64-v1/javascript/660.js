'use strict';

// 660. Remove 9: base-nine digits interpreted as decimal digits.
// O(log n) time and O(1) auxiliary space. Inputs are preserved.
function solve(n) {
  let answer = 0;
  let place = 1;
  let remaining = n;
  while (remaining > 0) {
    const digit = remaining % 9;
    remaining = Math.floor(remaining / 9);
    answer += digit * place;
    place *= 10;
  }
  return answer;
}

const newInteger = solve;
class Solution {
  newInteger(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, newInteger };
