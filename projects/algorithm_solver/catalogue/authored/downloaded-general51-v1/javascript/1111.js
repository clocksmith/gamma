'use strict';

// 1111. Maximum Nesting Depth of Two Valid Parentheses Strings (Medium).
// Specification: https://leetcode.com/problems/maximum-nesting-depth-of-two-valid-parentheses-strings/description/
function solve(seq) {
  const result = [];
  let depth = 0;
  for (const ch of seq) {
    if (ch === '(') { result.push(depth % 2); depth++; }
    else { depth--; result.push(depth % 2); }
  }
  return result;
}
const maxDepthAfterSplit = solve;
class Solution { maxDepthAfterSplit(seq) { return solve(seq); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDepthAfterSplit };
