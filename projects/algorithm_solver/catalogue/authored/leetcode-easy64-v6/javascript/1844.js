'use strict';

// 1844. Replace All Digits with Characters (Easy).
// Specification: https://leetcode.com/problems/replace-all-digits-with-characters/description/
// O(n) time and space; each odd-index digit shifts the preceding ASCII letter.
function solve(s) {
  const result = s.split('');
  for (let index = 1; index < s.length; index += 2) {
    const offset = s.charCodeAt(index) - 48;
    result[index] = String.fromCharCode(s.charCodeAt(index - 1) + offset);
  }
  return result.join('');
}

const replaceDigits = solve;
class Solution {
  replaceDigits(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceDigits };
