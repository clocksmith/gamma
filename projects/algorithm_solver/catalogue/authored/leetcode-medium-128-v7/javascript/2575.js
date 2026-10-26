'use strict';

// 2575. Find the Divisibility Array of a String: carry only the decimal prefix remainder rather than constructing huge integers.
// O(n) time and O(n) auxiliary space including the result; inputs are read-only.
function solve(word, m) {
  let remainder = 0;
  const result = [];
  for (const character of word) {
    remainder = (remainder * 10 + character.charCodeAt(0) - 48) % m;
    result.push(Number(remainder === 0));
  }
  return result;
}

const divisibilityArray = solve;
class Solution {
  divisibilityArray(word, m) { return solve(word, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, divisibilityArray };
