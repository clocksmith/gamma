'use strict';

// 1611. Make The String Great (Easy).
// Specification: https://leetcode.com/problems/make-the-string-great/description/
function solve(s) {
  const stack = [];
  for (const ch of s) {
    const top = stack.length > 0 ? stack[stack.length - 1] : null;
    if (top !== null && top !== ch && top.toLowerCase() === ch.toLowerCase()) stack.pop();
    else stack.push(ch);
  }
  return stack.join('');
}
const makeGood = solve;
class Solution { makeGood(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeGood };
