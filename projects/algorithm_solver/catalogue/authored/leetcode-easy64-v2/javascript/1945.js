'use strict';

// 1945. Sum of Digits of String After Convert (Easy).
// Specification: https://leetcode.com/problems/sum-of-digits-of-string-after-convert/description/
// O(n + k log(n + 1)) time, O(1) space; never construct the large encoded integer.
function solve(s, k) {
  let total = 0;
  for (const character of s) {
    const position = character.charCodeAt(0) - 96;
    total += Math.floor(position / 10) + position % 10;
  }
  for (let step = 1; step < k; step++) {
    let remaining = total;
    total = 0;
    while (remaining > 0) {
      total += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
  }
  return total;
}

const getLucky = solve;
class Solution {
  getLucky(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getLucky };
