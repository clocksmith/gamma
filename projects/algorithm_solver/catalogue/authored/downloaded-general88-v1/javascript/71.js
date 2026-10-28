'use strict';

// 71. Simplify Path (Medium).
// Specification: https://leetcode.com/problems/simplify-path/description/
function solve(path) {
  const stack = [];
  for (const part of path.split('/')) {
    if (part === '' || part === '.') continue;
    if (part === '..') stack.pop();
    else stack.push(part);
  }
  return '/' + stack.join('/');
}
const simplifyPath = solve;
class Solution { simplifyPath(path) { return solve(path); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, simplifyPath };
