'use strict';

// 3083. Existence of a Substring in a String and Its Reverse (Easy).
// Specification: https://leetcode.com/problems/existence-of-a-substring-in-a-string-and-its-reverse/description/
function solve(s) {
  const reversed = s.split('').reverse().join('');
  for (let i = 0; i + 1 < s.length; i++) {
    if (reversed.includes(s.slice(i, i + 2))) return true;
  }
  return false;
}
const isSubstringPresent = solve;
class Solution { isSubstringPresent(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSubstringPresent };
