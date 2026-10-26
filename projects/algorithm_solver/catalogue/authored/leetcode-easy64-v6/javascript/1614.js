'use strict';

// 1614. Maximum Nesting Depth of the Parentheses (Easy).
// Specification: https://leetcode.com/problems/maximum-nesting-depth-of-the-parentheses/description/
// O(n) time, O(1) space; input is a valid parentheses string.
function solve(s) {
  let depth = 0;
  let maximum = 0;
  for (const character of s) {
    if (character === '(') {
      depth++;
      maximum = Math.max(maximum, depth);
    } else if (character === ')') {
      depth--;
    }
  }
  return maximum;
}

const maxDepth = solve;
class Solution {
  maxDepth(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDepth };
