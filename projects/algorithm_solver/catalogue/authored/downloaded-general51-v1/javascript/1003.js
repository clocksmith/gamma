'use strict';

// 1003. Check If Word Is Valid After Substitutions (Medium).
// Specification: https://leetcode.com/problems/check-if-word-is-valid-after-substitutions/description/
function solve(s) {
  const stack = [];
  for (const ch of s) {
    stack.push(ch);
    while (stack.length >= 3 && stack[stack.length - 3] === 'a' && stack[stack.length - 2] === 'b' && stack[stack.length - 1] === 'c') stack.splice(-3);
  }
  return stack.length === 0;
}
const isValid = solve;
class Solution { isValid(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValid };
