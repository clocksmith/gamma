'use strict';

// 2696. Minimum String Length After Removing Substrings (Easy).
// Specification: https://leetcode.com/problems/minimum-string-length-after-removing-substrings/description/
function solve(s) {
  const stack = [];
  for (const ch of s) {
    const top = stack.length ? stack[stack.length - 1] : '';
    if ((top === 'A' && ch === 'B') || (top === 'C' && ch === 'D')) stack.pop();
    else stack.push(ch);
  }
  return stack.length;
}
const minLength = solve;
class Solution { minLength(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minLength };
