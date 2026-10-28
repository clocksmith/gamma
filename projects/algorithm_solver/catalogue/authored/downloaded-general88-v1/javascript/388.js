'use strict';

// 388. Longest Absolute File Path (Medium).
// Specification: https://leetcode.com/problems/longest-absolute-file-path/description/
function solve(input) {
  const stack = [];
  let best = 0;
  for (const line of input.split('\n')) {
    let depth = 0;
    while (depth < line.length && line[depth] === '\t') depth++;
    const name = line.slice(depth);
    while (stack.length > depth) stack.pop();
    stack.push(name);
    if (name.includes('.')) {
      const length = stack.reduce((sum, part) => sum + part.length, 0) + stack.length - 1;
      best = Math.max(best, length);
    }
  }
  return best;
}
const lengthLongestPath = solve;
class Solution { lengthLongestPath(input) { return solve(input); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthLongestPath };
