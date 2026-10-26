'use strict';

// 2165. Smallest Value of the Rearranged Number: sort negative magnitudes downward and place the first nonzero positive digit first.
// O(d log d) time and O(d) auxiliary space for d decimal digits; inputs are read-only.
function solve(num) {
  if (num === 0) return 0;
  const digits = String(Math.abs(num)).split('').sort();
  if (num < 0) return -Number(digits.reverse().join(''));
  let first = 0;
  while (digits[first] === '0') first += 1;
  [digits[0], digits[first]] = [digits[first], digits[0]];
  return Number(digits.join(''));
}

const smallestNumber = solve;
class Solution {
  smallestNumber(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestNumber };
