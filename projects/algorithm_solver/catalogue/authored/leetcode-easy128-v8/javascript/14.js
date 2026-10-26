'use strict';

// 14. Longest Common Prefix (Easy).
// Specification: https://leetcode.com/problems/longest-common-prefix/description/
// O(n * m) time, O(1) auxiliary space excluding the result; compare a shared prefix.
function solve(strs) {
  let length = strs[0].length;
  for (let index = 1; index < strs.length; index++) {
    length = Math.min(length, strs[index].length);
    let matched = 0;
    while (matched < length && strs[index][matched] === strs[0][matched]) matched++;
    length = matched;
    if (length === 0) break;
  }
  return strs[0].slice(0, length);
}

const longestCommonPrefix = solve;
class Solution {
  longestCommonPrefix(strs) { return solve(strs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestCommonPrefix };
