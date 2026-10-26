'use strict';

// 1663. Smallest String With A Given Numeric Value: place all extra letter value as far to the right as possible.
// O(n) time and O(n) space including the result; inputs are read-only.
function solve(n, k) {
  const letters = new Array(n).fill('a');
  let remaining = k - n;
  for (let index = n - 1; index >= 0; index -= 1) {
    const extra = Math.min(25, remaining);
    letters[index] = String.fromCharCode(97 + extra);
    remaining -= extra;
  }
  return letters.join('');
}

const getSmallestString = solve;
class Solution {
  getSmallestString(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSmallestString };
