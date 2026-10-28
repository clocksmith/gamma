'use strict';

// 1249. Minimum Remove to Make Valid Parentheses (Medium).
// Specification: https://leetcode.com/problems/minimum-remove-to-make-valid-parentheses/description/
function solve(s) {
  const remove = new Set();
  const stack = [];
  for (let i = 0; i < s.length; i++) {
    if (s[i] === '(') stack.push(i);
    else if (s[i] === ')') { if (stack.length === 0) remove.add(i); else stack.pop(); }
  }
  for (const index of stack) remove.add(index);
  let result = '';
  for (let i = 0; i < s.length; i++) { if (!remove.has(i)) result += s[i]; }
  return result;
}
const minRemoveToMakeValid = solve;
class Solution { minRemoveToMakeValid(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minRemoveToMakeValid };
