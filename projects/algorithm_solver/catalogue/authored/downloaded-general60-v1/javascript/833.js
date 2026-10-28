'use strict';

// 833. Find And Replace in String (Medium).
// Specification: https://leetcode.com/problems/find-and-replace-in-string/description/
function solve(s, indices, sources, targets) {
  const replacements = indices.map((index, i) => [index, sources[i], targets[i]]).sort((a, b) => b[0] - a[0]);
  let result = s;
  for (const [index, source, target] of replacements) {
    if (result.slice(index, index + source.length) === source) result = result.slice(0, index) + target + result.slice(index + source.length);
  }
  return result;
}
const findReplaceString = solve;
class Solution { findReplaceString(s, indices, sources, targets) { return solve(s, indices, sources, targets); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findReplaceString };
