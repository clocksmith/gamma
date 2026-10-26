'use strict';

// 1946. Largest Number After Mutating Substring: start at the first strict improvement and stop before the first decrease.
// O(n) time and O(n) space; inputs are read-only.
function solve(num, change) {
  const digits = num.split('');
  let index = 0;
  while (index < digits.length) {
    const digit = digits[index].charCodeAt(0) - 48;
    if (change[digit] > digit) break;
    index += 1;
  }
  while (index < digits.length) {
    const digit = digits[index].charCodeAt(0) - 48;
    if (change[digit] < digit) break;
    digits[index] = String(change[digit]);
    index += 1;
  }
  return digits.join('');
}

const maximumNumber = solve;
class Solution {
  maximumNumber(num, change) { return solve(num, change); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumNumber };
