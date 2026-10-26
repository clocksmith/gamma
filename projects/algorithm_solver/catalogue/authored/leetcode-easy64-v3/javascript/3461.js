'use strict';

// 3461. Check If Digits Are Equal in String After Operations I (Easy).
// Specification: https://leetcode.com/problems/check-if-digits-are-equal-in-string-after-operations-i/description/
// O(n^2) time, O(n) space; update a local digit buffer from left to right.
function solve(s) {
  const digits = Array.from(s, character => character.charCodeAt(0) - 48);
  let length = digits.length;
  while (length > 2) {
    for (let index = 0; index + 1 < length; index++) {
      digits[index] = (digits[index] + digits[index + 1]) % 10;
    }
    length--;
  }
  return digits[0] === digits[1];
}

const hasSameDigits = solve;
class Solution {
  hasSameDigits(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasSameDigits };
